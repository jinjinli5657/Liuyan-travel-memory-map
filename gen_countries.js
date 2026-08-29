const fs = require('fs');
const topojson = require('topojson-client');
const { geoCentroid } = require('d3-geo');
const wc = require('world-countries');

const topo = JSON.parse(fs.readFileSync('assets/countries-110m.json', 'utf8'));
const fc = topojson.feature(topo, topo.objects.countries);

// world-countries 索引：按 ccn3（3 位 numeric 字符串，去前导零后比较）
const byCcn3 = {};
wc.forEach(c => { if (c.ccn3) byCcn3[parseInt(c.ccn3, 10)] = c; });

const REGION_ZH = {
  Asia: '亚洲', Europe: '欧洲', Africa: '非洲',
  Americas: '美洲', Oceania: '大洋洲', Antarctic: '南极洲',
  Polar: '南极洲'
};

function flagEmoji(cc2) {
  if (!cc2 || cc2.length !== 2) return '🏳️';
  return String.fromCodePoint(...cc2.toUpperCase().split('').map(ch => 0x1F1E6 + ch.charCodeAt(0) - 65));
}

const master = [];
const alpha3ToNum = {};
const byCode = {};

fc.features.forEach(f => {
  const idNum = parseInt(f.id, 10);            // topojson id：numeric
  const w = byCcn3[idNum];
  if (!w) return;                              // 地图里有但世界主数据缺失 → 跳过
  let cen;
  try { cen = geoCentroid(f); } catch (e) { cen = null; }
  const lng = cen ? +cen[0].toFixed(4) : (w.latlng && w.latlng[1] != null ? w.latlng[1] : 0);
  const lat = cen ? +cen[1].toFixed(4) : (w.latlng && w.latlng[0] != null ? w.latlng[0] : 0);
  const rec = {
    code: w.cca3,
    code2: w.cca2,
    name_zh: (w.translations && w.translations.zho && w.translations.zho.common) || w.name.common,
    name_en: w.name.common,
    flag: flagEmoji(w.cca2),
    lat, lng,
    region: REGION_ZH[w.region] || '其他',
    numeric: String(idNum)
  };
  master.push(rec);
  alpha3ToNum[rec.code] = String(idNum);
  byCode[rec.code] = rec;
});

// 稳定排序（按英文名）
master.sort((a, b) => a.name_en.localeCompare(b.name_en));

const out =
`// ============================================================
// 世界国家主数据（自动生成，无需手动维护）
//   MASTER_COUNTRIES : 全部可标记国家（中英文名 / 旗帜 / 坐标 / 大洲）
//   ALPHA3_TO_NUMERIC: alpha-3 → world-atlas numeric（匹配地图 path.id）
//   MASTER_BY_CODE   : code(α3) → 国家记录，供弹窗/反查
// ============================================================
const ALPHA3_TO_NUMERIC = ${JSON.stringify(alpha3ToNum, null, 0)};
const MASTER_COUNTRIES = ${JSON.stringify(master, null, 0)};
const MASTER_BY_CODE = (function(){ const m={}; MASTER_COUNTRIES.forEach(c=>m[c.code]=c); return m; })();
`;

fs.writeFileSync('countries-data.js', out, 'utf8');
console.log('countries generated:', master.length);
console.log('sample:', JSON.stringify(master.slice(0, 3)));
// 统计缺失
const missing = fc.features.filter(f => !byCcn3[parseInt(f.id,10)]).map(f => f.properties && f.properties.name);
console.log('topojson 中未匹配 world-countries 的国家数:', missing.length, missing.slice(0,10));
