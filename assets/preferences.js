(() => {
  const themeSelect = document.getElementById('theme-select');
  const fontSelect = document.getElementById('font-select');
  if (!themeSelect || !fontSelect) return;
  const presets = {
    dm: {sans:'"DM Sans",sans-serif',display:'"Manrope",sans-serif',mono:'"DM Mono",monospace',href:''},
    inter: {sans:'"Inter",sans-serif',display:'"Inter",sans-serif',mono:'"JetBrains Mono",monospace',href:'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap'},
    plex: {sans:'"IBM Plex Sans",sans-serif',display:'"IBM Plex Sans",sans-serif',mono:'"IBM Plex Mono",monospace',href:'https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap'},
    source: {sans:'"Source Sans 3",sans-serif',display:'"Source Sans 3",sans-serif',mono:'"Source Code Pro",monospace',href:'https://fonts.googleapis.com/css2?family=Source+Code+Pro:wght@400;500;600&family=Source+Sans+3:wght@400;500;600;700&display=swap'},
    atkinson: {sans:'"Atkinson Hyperlegible",sans-serif',display:'"Atkinson Hyperlegible",sans-serif',mono:'"Atkinson Hyperlegible",sans-serif',href:'https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible:wght@400;700&display=swap'},
    space: {sans:'"Space Grotesk",sans-serif',display:'"Space Grotesk",sans-serif',mono:'"DM Mono",monospace',href:'https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&display=swap'}
  };
  const get=(k,d)=>{try{return localStorage.getItem(k)||d}catch(_){return d}};
  const put=(k,v)=>{try{localStorage.setItem(k,v)}catch(_){}};
  let link=document.getElementById('fieldnote-font-preset');
  function font(id){const p=presets[id]||presets.dm;const root=document.documentElement;root.style.setProperty('--sans',p.sans);root.style.setProperty('--display',p.display);root.style.setProperty('--mono',p.mono);if(p.href){if(!link){link=document.createElement('link');link.id='fieldnote-font-preset';link.rel='stylesheet';document.head.appendChild(link)}link.href=p.href}else if(link){link.remove();link=null}fontSelect.value=id;put('fieldnote-font',id)}
  function theme(pref){const resolved=pref==='system'?(matchMedia('(prefers-color-scheme: light)').matches?'light':'dark'):pref;document.documentElement.dataset.theme=['dark','light','forest'].includes(resolved)?resolved:'dark';themeSelect.value=pref;put('fieldnote-theme',pref)}
  themeSelect.addEventListener('change',()=>theme(themeSelect.value));fontSelect.addEventListener('change',()=>font(fontSelect.value));
  theme(get('fieldnote-theme','system'));font(get('fieldnote-font','dm'));
  matchMedia('(prefers-color-scheme: light)').addEventListener?.('change',()=>{if(get('fieldnote-theme','system')==='system')theme('system')});
})();
