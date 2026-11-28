// 목업 도우미: ?theme=light 로 라이트 모드, <i data-icon="이름" data-size="20"> 를 선 아이콘으로 바꾼다.
// 아이콘은 SF Symbols 를 흉내 낸 임시 그림이다. 실제 앱은 주석의 SF Symbol 이름을 쓴다.
(function () {
  var q = new URLSearchParams(location.search);
  if (q.get('theme') === 'light') document.documentElement.setAttribute('data-theme', 'light');
  var P = {
    // gauge.with.needle
    gauge: '<path d="M4 16a8 8 0 1 1 16 0"/><path d="M12 16l4-5"/><circle cx="12" cy="16" r="1.4" fill="currentColor"/>',
    // square.grid.2x2
    grid: '<rect x="4" y="4" width="7" height="7" rx="1.8"/><rect x="13" y="4" width="7" height="7" rx="1.8"/><rect x="4" y="13" width="7" height="7" rx="1.8"/><rect x="13" y="13" width="7" height="7" rx="1.8"/>',
    // gearshape
    gear: '<circle cx="12" cy="12" r="3"/><path d="M12 3v2.5M12 18.5V21M3 12h2.5M18.5 12H21M5.6 5.6l1.8 1.8M16.6 16.6l1.8 1.8M5.6 18.4l1.8-1.8M16.6 7.4l1.8-1.8"/>',
    // lock.fill
    lock: '<rect x="6" y="11" width="12" height="9" rx="2" fill="currentColor" stroke="none"/><path d="M8.5 11V8.5a3.5 3.5 0 0 1 7 0V11"/>',
    // checkmark
    check: '<path d="M6 12.5l4 4 8-9"/>',
    // chevron.right
    chev: '<path d="M10 6l6 6-6 6"/>',
    // arrow.up.right
    ext: '<path d="M8 16L16 8M9.5 8H16v6.5"/>',
    // stop.fill
    stop: '<rect x="7" y="7" width="10" height="10" rx="2" fill="currentColor" stroke="none"/>',
    // play.fill
    play: '<path d="M8 6l10 6-10 6z" fill="currentColor" stroke="none"/>',
    // bolt.fill
    bolt: '<path d="M13 3L6 13h5l-1 8 7-10h-5z" fill="currentColor" stroke="none"/>',
    // info.circle
    info: '<circle cx="12" cy="12" r="8.5"/><path d="M12 11v5"/><circle cx="12" cy="8" r=".9" fill="currentColor"/>',
    signal: '<path d="M4 18v-2M9 18v-5M14 18v-8M19 18V7" stroke-width="2.6"/>',
    wifi: '<path d="M4 10a12 12 0 0 1 16 0M7 13.5a7.5 7.5 0 0 1 10 0M10 17a3 3 0 0 1 4 0"/>',
    battery: '<rect x="2.5" y="7" width="17" height="10" rx="3"/><rect x="4.5" y="9" width="10" height="6" rx="1.4" fill="currentColor" stroke="none"/><path d="M21.5 10.5v3"/>',
    // xmark
    xmark: '<path d="M7 7l10 10M17 7L7 17"/>',
    // arrow.clockwise
    restart: '<path d="M18 12a6 6 0 1 1-2-4.5"/><path d="M16.5 4v4h-4"/>'
  };
  document.querySelectorAll('i[data-icon]').forEach(function (el) {
    var s = el.getAttribute('data-size') || 20;
    var w = el.getAttribute('data-w') || 1.8;
    el.outerHTML = '<svg aria-hidden="true" width="' + s + '" height="' + s + '" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="' + w + '" stroke-linecap="round" stroke-linejoin="round" style="flex:none;display:block">' + (P[el.getAttribute('data-icon')] || '') + '</svg>';
  });
})();
