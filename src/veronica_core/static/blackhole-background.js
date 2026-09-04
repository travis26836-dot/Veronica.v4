/* Close-up supermassive black hole behind the chat chrome. WebGL; 2D fallback. */
(function (root) {
  const VERT = "attribute vec2 a;void main(){gl_Position=vec4(a,0.0,1.0);}";
  const FRAG = `
precision highp float;
uniform vec2 u_res;
uniform float u_time;
uniform float u_still;

float hash(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
float noise(vec2 p){
  vec2 i=floor(p),f=fract(p);
  f=f*f*(3.0-2.0*f);
  return mix(mix(hash(i),hash(i+vec2(1.0,0.0)),f.x),mix(hash(i+vec2(0.0,1.0)),hash(i+vec2(1.0,1.0)),f.x),f.y);
}
float fbm(vec2 p){
  float v=0.0,a=0.5;
  for(int i=0;i<5;i++){v+=a*noise(p);p=p*2.03+vec2(4.1,9.3);a*=0.5;}
  return v;
}

vec3 accretion(vec2 p, float rs, float t, float incl){
  float dy=p.y/max(incl,0.08);
  float dr=length(vec2(p.x,dy));
  float band=smoothstep(rs*1.18,rs*1.45,dr)*smoothstep(rs*3.6,rs*2.15,dr);
  float thin=exp(-pow(abs(p.y)/(0.055+0.03*dr),2.0));
  float ang=atan(p.x,dy)-t*2.2/max(pow(dr,1.5),0.08);
  float lanes=0.55+0.45*sin(ang*14.0+fbm(vec2(dr*6.0,ang))*3.5);
  float doppler=clamp(0.5+0.72*p.x/max(dr,0.05),0.08,1.35);
  vec3 col=mix(vec3(0.35,0.06,0.03), vec3(1.0,0.55,0.18), clamp(doppler,0.0,1.0));
  col=mix(col, vec3(1.0,0.92,0.72), smoothstep(0.85,1.2,doppler));
  return col*band*thin*lanes*(0.45+1.1*doppler);
}

void main(){
  vec2 uv=(gl_FragCoord.xy-0.5*u_res)/u_res.y;
  float t=u_still>0.5?22.0:u_time*0.035;
  vec2 center=vec2(0.08,-0.06);
  vec2 p=uv-center;
  float r=length(p);
  float rs=0.46;

  float orbit=t*0.22;
  float cs=cos(orbit),sn=sin(orbit);
  vec2 bg=vec2(uv.x*cs-uv.y*sn, uv.x*sn+uv.y*cs);
  float dust=fbm(bg*1.35+vec2(t*0.05,-t*0.03));
  float arm=0.5+0.5*sin(atan(bg.y,bg.x)+length(bg)*1.8-t*0.4);
  vec3 galaxy=vec3(0.02,0.015,0.04);
  galaxy+=vec3(0.16,0.07,0.28)*dust*arm*smoothstep(1.6,0.15,length(bg));
  galaxy+=vec3(0.45,0.22,0.12)*pow(dust,2.0)*0.25;
  float speck=pow(noise(bg*38.0), 14.0);
  galaxy+=vec3(0.75,0.72,0.9)*speck*0.35;

  float lens=1.0+0.9*rs*rs/max(r*r,0.02);
  vec2 lp=p*lens;
  vec3 disk=accretion(lp, rs, t, 0.20);
  vec3 far=accretion(vec2(lp.x,-lp.y*0.92), rs, t+2.1, 0.20)*0.55*smoothstep(rs*1.05,rs*1.9,r);

  float ring=smoothstep(0.018,0.0,abs(r-rs*1.38));
  float ring2=smoothstep(0.03,0.0,abs(r-rs*1.38));
  vec3 photon=vec3(1.0,0.78,0.42)*ring*2.2+vec3(1.0,0.5,0.18)*ring2*0.45;
  photon*=0.55+0.7*clamp(p.x*1.4+0.5,0.2,1.2);

  float hole=smoothstep(rs*1.02,rs*0.88,r);
  vec3 col=galaxy;
  col=mix(col, disk+far, clamp(length(disk+far),0.0,1.0));
  col+=disk+far+photon;
  col*=mix(1.0,0.22,smoothstep(rs*2.4,rs*1.02,r));
  col=mix(vec3(0.0), col, 1.0-hole);
  col+=vec3(0.18,0.07,0.03)*smoothstep(rs*2.1,rs,r)*(1.0-hole)*0.4;
  gl_FragColor=vec4(col,1.0);
}`;

  function compile(gl, type, src) {
    const shader = gl.createShader(type);
    gl.shaderSource(shader, src);
    gl.compileShader(shader);
    if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) return null;
    return shader;
  }

  function startWebgl(canvas, reduceMotion) {
    const gl = canvas.getContext("webgl", { alpha: false, antialias: false, depth: false, stencil: false, premultipliedAlpha: false, powerPreference: "low-power" });
    if (!gl) return false;
    const vs = compile(gl, gl.VERTEX_SHADER, VERT);
    const fs = compile(gl, gl.FRAGMENT_SHADER, FRAG);
    if (!vs || !fs) return false;
    const program = gl.createProgram();
    gl.attachShader(program, vs);
    gl.attachShader(program, fs);
    gl.bindAttribLocation(program, 0, "a");
    gl.linkProgram(program);
    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) return false;
    const buf = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, buf);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
    gl.useProgram(program);
    gl.enableVertexAttribArray(0);
    gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 0, 0);
    const uRes = gl.getUniformLocation(program, "u_res");
    const uTime = gl.getUniformLocation(program, "u_time");
    const uStill = gl.getUniformLocation(program, "u_still");
    let raf = 0;
    const start = performance.now();
    const fit = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 1.75);
      const scale = Math.min(1, 1400 / Math.max(window.innerWidth, window.innerHeight));
      const w = Math.max(2, Math.floor(window.innerWidth * dpr * scale));
      const h = Math.max(2, Math.floor(window.innerHeight * dpr * scale));
      if (canvas.width !== w || canvas.height !== h) {
        canvas.width = w;
        canvas.height = h;
      }
      gl.viewport(0, 0, w, h);
      gl.uniform2f(uRes, w, h);
    };
    const frame = (now) => {
      fit();
      gl.uniform1f(uTime, (now - start) / 1000);
      gl.uniform1f(uStill, reduceMotion ? 1 : 0);
      gl.drawArrays(gl.TRIANGLES, 0, 3);
      if (!reduceMotion) raf = requestAnimationFrame(frame);
    };
    fit();
    frame(performance.now());
    window.addEventListener("resize", () => {
      if (reduceMotion) frame(performance.now());
    });
    document.addEventListener("visibilitychange", () => {
      if (document.hidden) {
        cancelAnimationFrame(raf);
      } else if (!reduceMotion) {
        raf = requestAnimationFrame(frame);
      }
    });
    return true;
  }

  function startCanvas2d(canvas, reduceMotion) {
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    const fit = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 1.5);
      canvas.width = Math.floor(window.innerWidth * dpr);
      canvas.height = Math.floor(window.innerHeight * dpr);
    };
    const paint = (t) => {
      const w = canvas.width;
      const h = canvas.height;
      ctx.setTransform(1, 0, 0, 1, 0, 0);
      ctx.fillStyle = "#07010d";
      ctx.fillRect(0, 0, w, h);
      const cx = w * 0.46;
      const cy = h * 0.58;
      const rs = Math.min(w, h) * 0.34;
      const spin = reduceMotion ? 0.4 : t * 0.00008;
      const disk = ctx.createRadialGradient(cx + rs * 0.22, cy, rs * 0.2, cx, cy, rs * 2.4);
      disk.addColorStop(0, "rgba(255,210,140,0.0)");
      disk.addColorStop(0.18, "rgba(255,170,80,0.0)");
      disk.addColorStop(0.28, "rgba(255,140,60,0.55)");
      disk.addColorStop(0.42, "rgba(180,60,20,0.28)");
      disk.addColorStop(1, "rgba(20,4,30,0)");
      ctx.save();
      ctx.translate(cx, cy);
      ctx.rotate(spin);
      ctx.scale(1, 0.22);
      ctx.translate(-cx, -cy);
      ctx.fillStyle = disk;
      ctx.fillRect(0, 0, w, h);
      ctx.restore();
      const hole = ctx.createRadialGradient(cx, cy, rs * 0.7, cx, cy, rs);
      hole.addColorStop(0, "#000");
      hole.addColorStop(0.86, "#000");
      hole.addColorStop(1, "rgba(40,12,8,0.0)");
      ctx.fillStyle = hole;
      ctx.beginPath();
      ctx.arc(cx, cy, rs, 0, Math.PI * 2);
      ctx.fill();
      ctx.strokeStyle = "rgba(255,196,110,0.55)";
      ctx.lineWidth = Math.max(2, rs * 0.018);
      ctx.beginPath();
      ctx.arc(cx, cy, rs * 1.48, 0, Math.PI * 2);
      ctx.stroke();
    };
    fit();
    if (reduceMotion) {
      paint(0);
      window.addEventListener("resize", () => { fit(); paint(0); });
      return;
    }
    const loop = (now) => { fit(); paint(now); requestAnimationFrame(loop); };
    requestAnimationFrame(loop);
  }

  root.startVeronicaHorizon = function startVeronicaHorizon(canvas) {
    if (!canvas) return;
    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (!startWebgl(canvas, reduceMotion)) startCanvas2d(canvas, reduceMotion);
  };
})(typeof window !== "undefined" ? window : globalThis);
