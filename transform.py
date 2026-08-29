# -*- coding: utf-8 -*-
import io, re

F = "index.html"
s = io.open(F, "r", encoding="utf-8").read()

def rep(old, new, n=1):
    global s
    c = s.count(old)
    assert c == n, "期望出现 %d 次，实际 %d 次：\n%r" % (n, c, old[:80])
    s = s.replace(old, new, n)
    print("OK 替换 (%d): %s" % (n, old[:50].replace(chr(10), ' ')))

# ---- R1: 载入国家主数据 ----
rep('  <script src="data.js"></script>',
    '  <script src="countries-data.js"></script>\n  <script src="data.js"></script>')

# ---- R2: 删除内联 ALPHA3_TO_NUMERIC（改用 countries-data.js） ----
rep('''    // ============================================
    // ISO 3166-1 alpha-3 → numeric（world-atlas TopoJSON 用的是 numeric 字符串）
    // 仅列出我的 39 个国家，其他国家需要时再加
    // ============================================
    const ALPHA3_TO_NUMERIC = {
      MEX:'484', PHL:'608', KHM:'116', LAO:'418', MYS:'458', MNG:'496',
      MMR:'104', THA:'764', IDN:'360', VNM:'704', CHN:'156',
      EGY:'818', KEN:'404', MAR:'504', NAM:'516',
      PER:'604', ECU:'218',
      IND:'356',
      AUT:'040', BEL:'056', ISL:'352', POL:'616', DNK:'208', DEU:'276',
      FRA:'250', CZE:'203', LVA:'428', LUX:'442', VAT:'336', MCO:'492',
      CHE:'756', ESP:'724', GRC:'300', HUN:'348', ITA:'380', PRT:'620',
      TUR:'792', ISR:'376', JOR:'400', RUS:'643'
    };
    // 梵蒂冈在 countries-110m 里可能没有（太小），特殊处理
    const SMALL_COUNTRIES = { VAT: 'ITA' }; // 数值缺 → 跟该国放一起''',
'''    // 梵蒂冈在 countries-110m 里可能没有（太小），特殊处理
    const SMALL_COUNTRIES = { VAT: 'ITA' }; // 数值缺 → 跟该国放一起
    // 注：ALPHA3_TO_NUMERIC / MASTER_COUNTRIES / MASTER_BY_CODE 现由 countries-data.js 提供（覆盖全世界 ~174 国）''')

# ---- R3: countryByCode 回退到主数据 ----
rep("    function countryByCode(code) { return myCountries.find(c => c.code === code); }",
    "    function countryByCode(code) { return myCountries.find(c => c.code === code) || (typeof MASTER_BY_CODE !== 'undefined' ? MASTER_BY_CODE[code] : null) || null; }")

# ---- R4: myCountries 的 localStorage key ----
rep("    const LS_KEY = 'tb_visited_cities_v1';",
    "    const LS_KEY = 'tb_visited_cities_v1';\n    const LS_MYCOUNTRIES = 'tb_mycountries_v1';")

# ---- R5: loadVisited 读取 myCountries + saveMyCountries ----
rep('''      } catch (e) {}
    }

    function saveVisited() {
      try { localStorage.setItem(LS_KEY, JSON.stringify(visitedCities)); } catch (e) {}
    }''',
'''      } catch (e) {}
      // 已去国家：从浏览器本地读取（分享版从零开始，默认空数组）
      try {
        const raw = localStorage.getItem(LS_MYCOUNTRIES);
        if (raw) { const a = JSON.parse(raw); if (Array.isArray(a) && a.length) myCountries = a; }
      } catch (e) {}
    }

    function saveVisited() {
      try { localStorage.setItem(LS_KEY, JSON.stringify(visitedCities)); } catch (e) {}
    }
    function saveMyCountries() {
      try { localStorage.setItem(LS_MYCOUNTRIES, JSON.stringify(myCountries)); } catch (e) {}
    }''')

# ---- R6: 国家 path 加点击 + 指针 ----
rep('''      mapG.selectAll('.country')
        .data(countries.features)
        .join('path')
        .attr('class', d => `country ${visitedIds.has(d.id) ? 'visited' : ''}`)
        .attr('data-code', d => NUMERIC_TO_ALPHA3[d.id] || '')
        .attr('d', pathGen);''',
'''      mapG.selectAll('.country')
        .data(countries.features)
        .join('path')
        .attr('class', d => `country ${visitedIds.has(d.id) ? 'visited' : ''}`)
        .attr('data-code', d => NUMERIC_TO_ALPHA3[d.id] || '')
        .attr('d', pathGen)
        .style('cursor', 'pointer')
        .on('click', (event, d) => openCountryFromFeature(d));''')

# ---- R7: renderMarkers 先清国旗 ----
rep('''    function renderMarkers() {
      myCountries.forEach(c => {''',
'''    function renderMarkers() {
      markerLayer.querySelectorAll('.country-marker').forEach(n => n.remove());
      myCountries.forEach(c => {''')

# ---- R8: showCountryPopup 整体重写（支持标记/取消 + 手动加城市） ----
NEW_FN = r'''    function showCountryPopup(c) {
      hidePopup();
      hideHoverCard();
      const code = c.code;
      const master = (typeof CITY_MASTER !== 'undefined' && CITY_MASTER[code]) || [];
      const isVisited = myCountries.some(x => x.code === code);
      const clat = c.lat, clng = c.lng;
      const selCount = () => visitedCities.filter(v => v.country_code === code).length;

      const el = document.createElement('div');
      el.className = 'popup country-popup';
      el.style.left = '24px';
      el.style.top  = '110px';
      el.innerHTML = `
        <button class="popup-close">×</button>
        <div class="flag">${c.flag}</div>
        <h3>${titleWithDate(c.name_zh, getContent('country:' + code))}</h3>
        <span class="region-tag">${c.region}</span>
        <button class="mark-btn ${isVisited ? 'on' : ''}" id="markBtn">${isVisited ? '✓ 已标记来过（点此取消）' : '＋ 标记我来过'}</button>
        <div class="place-section"></div>
        <div class="city-count">已选 <strong class="sel-count">${selCount()}</strong> / 共 ${master.length} 个城市</div>
        <input class="city-filter" type="text" placeholder="筛选城市…" />
        <div class="city-checklist"></div>
        <div class="add-city-row">
          <input class="add-city-input" type="text" placeholder="没有你的城市？手动添加…" />
          <button class="add-city-btn">添加</button>
        </div>
        <button class="export-btn">导出已选 → data.js</button>
      `;
      el.addEventListener('wheel', e => e.stopPropagation());

      const checklist = el.querySelector('.city-checklist');
      const filterInput = el.querySelector('.city-filter');
      const selCountEl = el.querySelector('.sel-count');

      function renderList() {
        const f = (filterInput.value || '').trim().toLowerCase();
        const items = master
          .filter(city => !f || city.name.toLowerCase().includes(f))
          .map(city => {
            const key = code + '|' + city.name;
            const on = visitedSet.has(key);
            return `<div class="city-check ${on ? 'on' : ''}">
              <label class="city-check-label">
                <input type="checkbox" class="city-check-input" data-key="${key}" ${on ? 'checked' : ''} />
                <span>${city.name}</span>
              </label>
              ${on ? `<button class="city-edit" data-key="${key}" title="编辑该城市简介/照片">✎</button>` : ''}
            </div>`;
          }).join('');
        checklist.innerHTML = items || '<div class="empty">这个国家还没有内置城市，用下面的框手动添加即可</div>';
      }
      renderList();
      filterInput.addEventListener('input', renderList);

      checklist.addEventListener('click', (e) => {
        const btn = e.target.closest('.city-edit');
        if (!btn) return;
        e.stopPropagation();
        const key = btn.dataset.key;
        const [cc, name] = key.split('|');
        const city = master.find(m => (cc + '|' + m.name) === key);
        if (city) {
          const coords = latLngToXY(city.lat, city.lng) || { x: 80, y: 200 };
          showCityPopup({ country_code: cc, name: city.name, lat: city.lat, lng: city.lng }, coords);
        }
      });

      checklist.addEventListener('change', (e) => {
        const cb = e.target.closest('input[type=checkbox]');
        if (!cb) return;
        const key = cb.dataset.key;
        const [cc, name] = key.split('|');
        if (cb.checked) {
          const city = master.find(m => (cc + '|' + m.name) === key);
          if (city && !visitedSet.has(key)) {
            visitedSet.add(key);
            visitedCities.push({ country_code: cc, name: city.name, lat: city.lat, lng: city.lng });
          }
        } else {
          visitedSet.delete(key);
          visitedCities = visitedCities.filter(v => (v.country_code + '|' + v.name) !== key);
        }
        saveVisited();
        refreshQuickBadge();
        persistToServer();
        renderCityMarkers();
        updateCityCount();
        selCountEl.textContent = selCount();
        cb.closest('.city-check').classList.toggle('on', cb.checked);
      });

      // 标记 / 取消标记国家
      el.querySelector('#markBtn').onclick = (e) => {
        e.stopPropagation();
        if (myCountries.some(x => x.code === code)) {
          if (!confirm('取消标记「' + c.name_zh + '」？该国及其所有城市的记录都会被删除。')) return;
          myCountries = myCountries.filter(x => x.code !== code);
          visitedCities = visitedCities.filter(v => v.country_code !== code);
          visitedSet = new Set(visitedCities.map(v => v.country_code + '|' + v.name));
          delete placeContent['country:' + code];
        } else {
          myCountries.push({ code: c.code, code2: c.code2, name_zh: c.name_zh, name_en: c.name_en, flag: c.flag, lat: c.lat, lng: c.lng, region: c.region });
        }
        saveMyCountries();
        refreshAfterCountryChange();
        showCountryPopup(c);   // 重新打开刷新按钮状态
      };

      // 手动添加城市
      el.querySelector('.add-city-btn').onclick = (e) => {
        e.stopPropagation();
        const inp = el.querySelector('.add-city-input');
        const name = (inp.value || '').trim();
        if (!name) return;
        if (!CITY_MASTER[code]) CITY_MASTER[code] = [];
        if (!CITY_MASTER[code].some(m => m.name === name)) CITY_MASTER[code].push({ name, lat: clat, lng: clng });
        const key = code + '|' + name;
        if (!visitedSet.has(key)) {
          visitedSet.add(key);
          visitedCities.push({ country_code: code, name, lat: clat, lng: clng });
        }
        saveVisited();
        refreshQuickBadge();
        persistToServer();
        renderCityMarkers();
        updateCityCount();
        showCountryPopup(c);  // 刷新列表
      };

      el.querySelector('.popup-close').onclick = hidePopup;
      el.querySelector('.place-section').appendChild(buildPlaceSection('country:' + code));
      el.querySelector('.export-btn').onclick = (e) => {
        e.stopPropagation();
        showExportModal();
      };

      mapWrap.appendChild(el);
      currentPopup = el;
    }'''

p8 = re.compile(r"(    function showCountryPopup\(c, coords\) \{).*?(      mapWrap\.appendChild\(el\);\n      currentPopup = el;\n    \})\n\n    function showExportModal\(\) \{", re.DOTALL)
assert p8.search(s), "showCountryPopup 未匹配"
s = p8.sub(lambda m: m.group(1) + NEW_FN + "\n\n    function showExportModal() {", s, count=1)
print("OK 重写 showCountryPopup")

# ---- R9: 辅助函数（recolor / open / refresh） ----
rep('    function hidePopup() {',
'''    function recolorCountries() {
      if (!mapG) return;
      const vids = new Set(myCountries.map(c => ALPHA3_TO_NUMERIC[c.code]).filter(Boolean));
      mapG.selectAll('.country').classed('visited', d => vids.has(d.id));
    }
    function openCountryFromFeature(d) {
      const code = NUMERIC_TO_ALPHA3[d.id];
      if (!code) return;
      const rec = (typeof MASTER_BY_CODE !== 'undefined' && MASTER_BY_CODE[code]) || null;
      if (rec) showCountryPopup(rec);
    }
    function refreshAfterCountryChange() {
      recolorCountries();
      renderMarkers();
      renderCityMarkers();
      drawRoutes();
      recomputeTimeline();
      updateStats();
      updateCityCount();
      refreshQuickBadge();
    }

    function hidePopup() {''')

# ---- R10: 持久化改为 localStorage（去掉 save-server） ----
START = "    // ============================================\n    // 自动保存：把当前「勾选城市 + 地点文字/照片」静默写进磁盘 saved-state.js"
END = ("    function pingSaveServer() {\n"
       "      postJson(SAVE_ENDPOINT, JSON.stringify({ ping: 1 })).then(res => {\n"
       "        if (res.ok) setAutosaveStatus(true, null);\n"
       "        else setAutosaveStatus(false, (res.via + ' 被拦截 (HTTP ' + (res.status || '?') + ') · ' + (res.error || '') + ' ｜ curl 已确认服务正常 → 试 Safari').slice(0, 200));\n"
       "      });\n"
       "    }")
NEW_PERSIST = '''    // ============================================
    // 自动保存：数据只存在「你自己的浏览器本地」（localStorage），不依赖任何服务器。
    // 别人各用各的浏览器，互不可见；可用「💾 备份数据」导出 JSON 带走 / 恢复。
    // ============================================
    function setAutosaveStatus(ok, detail) {
      const el = document.getElementById('autosaveStatus');
      if (!el) return;
      if (detail) { el.title = '说明：' + detail; } else { el.removeAttribute('title'); }
      if (ok === null) { el.textContent = '自动保存：准备中…'; el.className = 'autosave-status connecting'; }
      else if (ok)     { el.textContent = '✓ 已自动保存到本地浏览器'; el.className = 'autosave-status ok'; }
      else             { el.textContent = '⚠ 本地空间不足，请用「💾 备份数据」导出'; el.className = 'autosave-status warn'; }
    }
    let _saveTimer = null;
    function persistToServer() {
      clearTimeout(_saveTimer);
      _saveTimer = setTimeout(() => {
        try {
          localStorage.setItem(LS_KEY, JSON.stringify(visitedCities));
          localStorage.setItem(LS_CONTENT, JSON.stringify(placeContent));
          saveMyCountries();
          setAutosaveStatus(true, null);
        } catch (e) {
          setAutosaveStatus(false, '浏览器本地空间不足（照片过多），请点「💾 备份数据」导出 JSON 留底');
        }
      }, 800);
    }'''
p10 = re.compile(re.escape(START) + r".*?" + re.escape(END), re.DOTALL)
assert p10.search(s), "持久化块未匹配"
s = p10.sub(NEW_PERSIST, s, count=1)
print("OK 重写持久化块")

# ---- R11: 启动处去掉 pingSaveServer ----
rep('''    pingSaveServer();
    persistToServer();''',
'''    setAutosaveStatus(null);
    persistToServer();''')

# ---- R12: CSS 新增 mark-btn / add-city / 指针 ----
rep('    .export-btn:hover { background: #a5652c; }',
'''    .export-btn:hover { background: #a5652c; }
    .country { cursor: pointer; }
    .mark-btn {
      display: block; width: 100%; margin: 4px 0 8px; padding: 9px;
      border: none; border-radius: 9px; cursor: pointer;
      font-size: 13px; font-weight: 600;
      background: #e8eef6; color: #2b6cb0;
      transition: background 0.15s, color 0.15s;
    }
    .mark-btn:hover { background: #d7e3f4; }
    .mark-btn.on { background: #b87333; color: #fff; }
    .mark-btn.on:hover { background: #a5652c; }
    .add-city-row { display: flex; gap: 6px; margin: 6px 0; }
    .add-city-input {
      flex: 1; min-width: 0; padding: 7px 9px; border: 1px solid #e3dccd;
      border-radius: 8px; font-size: 13px;
    }
    .add-city-btn {
      flex: none; padding: 7px 12px; border: none; border-radius: 8px;
      background: #b87333; color: #fff; font-size: 13px; cursor: pointer;
    }
    .add-city-btn:hover { background: #a5652c; }''')

# ---- R13: 备份导出含 myCountries ----
rep('''        visitedCities: visitedCities,
        placeContent: placeContent
      };''',
'''        visitedCities: visitedCities,
        placeContent: placeContent,
        myCountries: myCountries
      };''')

# ---- R14: 恢复含 myCountries ----
rep('''          if (Array.isArray(data.visitedCities)) {
            visitedCities = data.visitedCities;
            visitedSet = new Set(visitedCities.map(v => v.country_code + '|' + v.name));
            saveVisited();
            refreshQuickBadge();
          }''',
'''          if (Array.isArray(data.visitedCities)) {
            visitedCities = data.visitedCities;
            visitedSet = new Set(visitedCities.map(v => v.country_code + '|' + v.name));
            saveVisited();
            refreshQuickBadge();
          }
          if (Array.isArray(data.myCountries)) {
            myCountries = data.myCountries;
            saveMyCountries();
          }''')

# ---- R15: 恢复后重绘地图/航线/统计 ----
rep('''          renderCityMarkers();
          updateCityCount();
          document.getElementById('cityCount').textContent = visitedCities.length;
          refreshQuickBadge();
          persistToServer();''',
'''          recolorCountries();
          renderMarkers();
          renderCityMarkers();
          drawRoutes();
          recomputeTimeline();
          updateStats();
          updateCityCount();
          document.getElementById('countryCount').textContent = myCountries.length;
          document.getElementById('cityCount').textContent = visitedCities.length;
          refreshQuickBadge();
          persistToServer();''')

# ---- R16: 统计抽成 updateStats() ----
rep('''    // ============================================
    // 统计
    // ============================================
    document.getElementById('countryCount').textContent = myCountries.length;
    document.getElementById('cityCount').textContent = visitedCities.length;

    const regionCount = {};
    myCountries.forEach(c => { regionCount[c.region] = (regionCount[c.region] || 0) + 1; });
    document.getElementById('regionStats').innerHTML = Object.entries(regionCount)
      .sort((a, b) => b[1] - a[1])
      .map(([r, n]) => `<div class="region-line"><span>${r}</span><span class="count">${n}</span></div>`)
      .join('');''',
'''    // ============================================
    // 统计
    // ============================================
    function updateStats() {
      document.getElementById('countryCount').textContent = myCountries.length;
      document.getElementById('cityCount').textContent = visitedCities.length;
      const regionCount = {};
      myCountries.forEach(c => { regionCount[c.region] = (regionCount[c.region] || 0) + 1; });
      document.getElementById('regionStats').innerHTML = Object.entries(regionCount)
        .sort((a, b) => b[1] - a[1])
        .map(([r, n]) => `<div class="region-line"><span>${r}</span><span class="count">${n}</span></div>`)
        .join('');
    }
    updateStats();''')

# ---- R17: 帮助文案更新 ----
rep('      <p style="margin-top:6px;">想永久备份：在国家弹窗点"导出已选 → data.js"→"下载 data.js"，连简介和照片一起存进文件。</p>',
    '      <p style="margin-top:6px;">想永久备份或换电脑：点右下角 <code>💾 备份数据</code> 下载一个 JSON（含城市、简介、照片），在别处用 <code>📂 恢复数据</code> 导入即可。</p>')
rep('''      <h3>🌍 添加新国家</h3>
      <p>在 <code>myCountries</code> 里 push 一条新国家记录，浏览器刷新就能看到新标记。</p>''',
'''      <h3>🌍 标记去过的国家</h3>
      <p>直接在地图上<strong>点任意国家</strong>（不需要改任何文件），弹窗里点 <code>＋ 标记我来过</code> 即可——该国立刻上色、出现在统计里；再点一次可取消。城市清单从内置主数据自动带出，没有的城市也能手动添加。</p>''')
rep('      <p>选完后，在国家弹窗里点"导出已选 → data.js"，把生成的数据发给我，我帮你永久写进 <code>data.js</code>（方便备份/换电脑）。</p>',
    '      <p>选完后数据已自动存在本浏览器；想长期保留或换设备，用右下角 <code>💾 备份数据</code> 导出 JSON 即可。</p>')
rep('      <p style="margin-top:8px;color:#3a7;">✅ 只要你勾城市 / 保存简介，页面会<strong>自动静默写盘</strong>（需保持本机自动保存服务在运行）。数据不再只依赖浏览器缓存，换方式打开也多半能找回。</p>',
    '      <p style="margin-top:8px;color:#3a7;">✅ 只要你勾城市 / 保存简介 / 标记国家，页面会<strong>自动存进你自己的浏览器</strong>。别人用同一份工具、各自浏览器互不可见；用「💾 备份数据」才能把数据带走或换电脑。</p>')

io.open(F, "w", encoding="utf-8").write(s)
print("=== index.html 转换完成，字节数:", len(s), "===")
