/* Acknowledged deletion is followed by a local, cancellable farewell scene. */
const SoulFarewell = (() => {
  const atlas = new Image();
  atlas.src = '/static/soul-portraits.png';
  let pending = null, live = null;
  const palette = ['#ffbb42', '#ef8c22', '#d85819', '#f4a52f', '#ffd877'];

  function cancel() {
    if (live) { live.finish(); return; }
    const old = pending;
    pending = null;
    if (old?.audio && old.audio.state !== 'closed') old.audio.close().catch(() => {});
  }

  // Called inside the confirming click so browsers may unlock audio. It remains
  // silent until the server acknowledges that forgetting actually succeeded.
  function prepare(person, volume) {
    cancel();
    const entry = { person: { ...person }, volume: Math.max(0, Math.min(1, volume)), audio: null };
    pending = entry;
    try {
      const Audio = window.AudioContext || window.webkitAudioContext;
      if (Audio) {
        entry.audio = new Audio();
        entry.audio.resume().catch(() => {});
      }
    } catch { /* The visual scene still works without audio support. */ }
  }

  function score(audio, volume) {
    if (!audio || audio.state !== 'running') return null;
    const gain = audio.createGain();
    gain.gain.value = volume * .24;
    const compressor = audio.createDynamicsCompressor();
    compressor.threshold.value = -20;
    compressor.knee.value = 18;
    compressor.ratio.value = 4;
    compressor.attack.value = .01;
    compressor.release.value = .4;
    gain.connect(compressor); compressor.connect(audio.destination);
    const orchestra = audio.createGain();
    orchestra.connect(gain);
    const hall = audio.createConvolver(), wet = audio.createGain();
    const impulse = audio.createBuffer(2, audio.sampleRate * 3, audio.sampleRate);
    for (let channel=0;channel<2;channel++) {
      const data=impulse.getChannelData(channel);
      for(let i=0;i<data.length;i++) data[i]=(Math.random()*2-1)*Math.pow(1-i/data.length,3.5)*.45;
    }
    hall.buffer=impulse; wet.gain.value=.3;
    orchestra.connect(hall); hall.connect(wet); wet.connect(gain);
    const now = audio.currentTime + .08;
    orchestra.gain.setValueAtTime(.65,now);
    orchestra.gain.linearRampToValueAtTime(1.25,now+8.3);
    orchestra.gain.setValueAtTime(1.1,now+10.8);
    orchestra.gain.exponentialRampToValueAtTime(.001,now+14.7);
    function voice(frequency,start,length,strength,type,attack,detune=0) {
      const tone=audio.createOscillator(),envelope=audio.createGain();
      tone.type=type;tone.frequency.value=frequency;tone.detune.value=detune;
      envelope.gain.setValueAtTime(0, now + start);
      envelope.gain.linearRampToValueAtTime(strength, now + start + attack);
      envelope.gain.exponentialRampToValueAtTime(.0001, now + start + length);
      tone.connect(envelope); envelope.connect(orchestra);
      tone.start(now + start); tone.stop(now + start + length + .05);
      tone.onended = () => { tone.disconnect(); envelope.disconnect(); };
    }
    function piano(frequency,start,strength=.6,length=3.2) {
      // Hammer attack and rapidly decaying upper partials, not a sustained beep.
      [1,.34,.16,.07,.025].forEach((amp,i)=>voice(frequency*(i+1),start,length/(1+i*.4),strength*amp,'sine',.008));
    }
    function strings(frequency,start,length,strength) {
      const envelope=audio.createGain(),filter=audio.createBiquadFilter();
      filter.type='lowpass';filter.frequency.setValueAtTime(650,now+start);
      filter.frequency.linearRampToValueAtTime(1700,now+start+length*.45);
      filter.frequency.linearRampToValueAtTime(450,now+start+length);
      envelope.gain.setValueAtTime(0,now+start);
      envelope.gain.linearRampToValueAtTime(strength,now+start+.9);
      envelope.gain.linearRampToValueAtTime(strength*.8,now+start+length*.65);
      envelope.gain.exponentialRampToValueAtTime(.0001,now+start+length);
      filter.connect(envelope);envelope.connect(orchestra);
      const oscillators=[-7,7].map(detune=>{const o=audio.createOscillator();o.type='sawtooth';o.frequency.value=frequency;o.detune.value=detune;o.connect(filter);o.start(now+start);o.stop(now+start+length+.05);return o;});
      const vibrato=audio.createOscillator(),depth=audio.createGain();
      vibrato.frequency.value=4.7;depth.gain.value=3;
      vibrato.connect(depth);oscillators.forEach(o=>depth.connect(o.detune));
      vibrato.start(now+start);vibrato.stop(now+start+length+.05);
      vibrato.onended=()=>{oscillators.forEach(o=>o.disconnect());vibrato.disconnect();depth.disconnect();filter.disconnect();envelope.disconnect();};
    }
    // D minor funeral phrase with a dominant A-major tension before returning home.
    const chords=[[73.416,146.832,174.614,220],[58.270,116.541,146.832,174.614],
      [55,110,138.591,164.814],[73.416,146.832,174.614,220]];
    chords.forEach((chord,i)=>{
      const start=i*3.1;
      voice(chord[0],start,4.2,.65,'sine',.16);
      chord.slice(1).forEach(f=>strings(f,start,4.3,.065));
      piano(chord[0]*2,start,.33,3.6);
      [0,1,2,1].forEach((step,j)=>piano(chord[step+1]*2,start+j*.68,.19,2.2));
    });
    [[293.665,.45],[349.228,1.65],[329.628,2.6],[293.665,3.7],
      [261.626,4.6],[233.082,5.6],[277.183,6.65],[329.628,7.6],
      [440,8.55],[349.228,9.6],[329.628,10.5],[293.665,11.45]].forEach(([f,t],i)=>{
        piano(f,t,i===8?.95:.65,3.4);
        if(i>=6)strings(f/2,t,2.5,.035);
      });
    return gain;
  }

  function show() {
    if (!pending) return Promise.resolve();
    const entry = pending;
    pending = null;
    return new Promise(resolve => {
      const previousFocus = document.activeElement;
      const dialog = document.createElement('dialog');
      dialog.className = 'farewell-scene';
      dialog.setAttribute('aria-labelledby', 'farewell-name');
      dialog.setAttribute('aria-describedby', 'farewell-description');
      dialog.innerHTML = `<div class="farewell-glow" aria-hidden="true"></div>
        <div class="farewell-top"><span>EL REGRESO · SON VİDA</span><button type="button" class="farewell-close" aria-label="Animasiya və musiqini bitir">Bağla ×</button></div>
        <div class="farewell-content"><p class="farewell-eyebrow">LƏÇƏKLƏRİN APARDIĞI XATİRƏ</p>
          <h2 id="farewell-name"></h2><div class="farewell-art" aria-hidden="true"><canvas width="720" height="500"></canvas></div>
          <p id="farewell-description">Son işıq sönür. Ruh cempasúchil ləçəklərinə qarışır.</p>
          <p class="farewell-last" role="status"></p>
        </div><div class="farewell-bottom"><button type="button" class="farewell-mute" aria-pressed="false">♫ Musiqini susdur</button><span>Bir gecə, hər il. İndi isə vida.</span></div>`;
      dialog.querySelector('#farewell-name').textContent = entry.person.display || 'Son vida';
      const canvas = dialog.querySelector('canvas'), ctx = canvas.getContext('2d');
      const mute = dialog.querySelector('.farewell-mute');
      let raf = 0, finishTimer = 0, endingTimer = 0, closed = false;
      let music = null, muted = entry.volume === 0;
      const motionReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      const duration = motionReduced ? 4200 : 15500;
      const scrollOverflow = document.documentElement.style.overflow;
      const finish = () => {
        if (closed) return;
        closed = true; cancelAnimationFrame(raf); clearTimeout(finishTimer); clearTimeout(endingTimer);
        if (entry.audio && entry.audio.state !== 'closed') entry.audio.close().catch(() => {});
        document.documentElement.style.overflow = scrollOverflow;
        dialog.close(); dialog.remove(); live = null;
        if (previousFocus?.isConnected) previousFocus.focus();
        resolve();
      };
      live = { finish };
      dialog.querySelector('.farewell-close').onclick = finish;
      dialog.addEventListener('cancel', event => { event.preventDefault(); finish(); });
      mute.onclick = () => {
        muted = !muted;
        if (music) music.gain.setTargetAtTime(muted ? 0 : entry.volume * .24, entry.audio.currentTime, .12);
        mute.setAttribute('aria-pressed', String(muted));
        mute.textContent = muted ? '♫ Musiqini aç' : '♫ Musiqini susdur';
      };
      document.body.append(dialog);
      document.documentElement.style.overflow = 'hidden';
      dialog.showModal();
      dialog.querySelector('.farewell-close').focus();
      // Resume may still be settling after the confirming gesture.
      const beginMusic = () => {
        if (closed) return;
        music = score(entry.audio, entry.volume);
        if (!music) { mute.disabled = true; mute.textContent = 'Səs bu brauzerdə əlçatan deyil'; }
        else if (muted) { mute.setAttribute('aria-pressed', 'true'); mute.textContent = '♫ Musiqini aç'; }
      };
      if (entry.audio) entry.audio.resume().then(beginMusic).catch(beginMusic);
      else beginMusic();

      const tiles = [];
      const columns = 18, rows = 24, width = 216, height = 288;
      for (let row = 0; row < rows; row++) for (let col = 0; col < columns; col++) {
        tiles.push({ col, row, start: 1.7 + (rows - row) / rows * 4 + Math.random() * 1.2,
          vx: (Math.random() - .5) * 160, vy: 35 + Math.random() * 55,
          turn: (Math.random() - .5) * 5, phase: Math.random() * Math.PI * 2,
          color: palette[Math.floor(Math.random() * palette.length)] });
      }
      const dust = Array.from({length: 65}, () => ({x:Math.random()*720,y:Math.random()*500,s:2+Math.random()*5,p:Math.random()*6}));
      const started = performance.now();
      function petal(x,y,size,angle,color,alpha) {
        ctx.save(); ctx.translate(x,y); ctx.rotate(angle); ctx.globalAlpha=alpha;
        ctx.fillStyle=color; ctx.beginPath(); ctx.moveTo(0,-size);
        ctx.bezierCurveTo(size*1.2,-size*.6,size*.8,size*.8,0,size);
        ctx.bezierCurveTo(-size*.65,size*.5,-size*.7,-size*.65,0,-size);ctx.fill();
        ctx.strokeStyle='#ffd57a';ctx.lineWidth=.55;ctx.beginPath();ctx.moveTo(0,-size*.65);ctx.lineTo(0,size*.65);ctx.stroke();ctx.restore();
      }
      function paint(timestamp) {
        const t=(timestamp-started)/1000, tileW=width/columns,tileH=height/rows;
        ctx.clearRect(0,0,720,500);
        const ready=atlas.complete&&atlas.naturalWidth>0;
        const sourceW=atlas.naturalWidth/4, sourceH=atlas.naturalHeight;
        const portrait=Math.max(0,Math.min(3,Number(entry.person.portrait)||0));
        if(motionReduced){
          ctx.globalAlpha=Math.max(0,1-t/3.5);
          if(ready)ctx.drawImage(atlas,portrait*sourceW,0,sourceW,sourceH,252,80,width,height);
          else {ctx.fillStyle='#f6deb3';ctx.font='76px Georgia';ctx.textAlign='center';ctx.fillText((entry.person.display||'R')[0],360,240);}
          ctx.globalAlpha=1;
        } else {
          const fade=Math.min(1,t*1.4);
          dust.forEach(d=>petal(d.x+Math.sin(t*.5+d.p)*18,(d.y-t*18+1000)%500,d.s,d.p+t*.35,'#b96124',fade*.28));
          tiles.forEach(tile=>{
            const age=t-tile.start, x=252+tile.col*tileW,y=80+tile.row*tileH;
            if(age<.4){
              ctx.globalAlpha=fade*Math.min(1,Math.max(0,1-age/.4));
              if(ready)ctx.drawImage(atlas,portrait*sourceW+tile.col*sourceW/columns,tile.row*sourceH/rows,sourceW/columns,sourceH/rows,x,y,tileW+.4,tileH+.4);
              else {ctx.fillStyle=tile.color;ctx.fillRect(x,y,tileW,tileH);}
              ctx.globalAlpha=1;
            }
            if(age>=0&&age<6.5){
              const alpha=Math.min(1,age*4)*Math.max(0,1-age/6.5);
              petal(x+tileW/2+tile.vx*age*.55+Math.sin(age*1.8+tile.phase)*age*7,
                y+tileH/2-tile.vy*age+Math.sin(age+tile.phase)*12,4+Math.sin(tile.phase)*1.5,tile.phase+age*tile.turn,tile.color,alpha);
            }
          });
        }
        if(!closed)raf=requestAnimationFrame(paint);
      }
      if(ctx)raf=requestAnimationFrame(paint);
      else dialog.querySelector('.farewell-art').textContent='✿';
      endingTimer=setTimeout(()=>{dialog.querySelector('.farewell-last').textContent='Ruh uzaqlaşdı. Xatirələr silindi.';},motionReduced?2900:10500);
      finishTimer=setTimeout(finish,duration);
    });
  }
  window.addEventListener('pagehide', cancel);
  return { prepare, show, cancel };
})();
