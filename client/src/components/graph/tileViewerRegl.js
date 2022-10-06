var imageTexture = new Image();

   imageTexture.src = '/return-files/1'; 


export default function drawTilesRegl(regl) {
  return regl({
    vert: `

    precision mediump float;
    attribute vec2 position;
    attribute vec2 aVertexTextureCoords;
    uniform mat3 projView;
    varying vec2 vTextureCoord;
    void main() {
      vTextureCoord = aVertexTextureCoords;
      vec3 xy = projView * vec3(position, 1.);
      gl_Position = vec4(xy.xy, 0, 1);
    }`,

    frag: `
    precision mediump float;
 
    uniform sampler2D imageTXT;

    varying vec2 vTextureCoord;

    void main() {
        vec4 tileColor=texture2D(imageTXT, vTextureCoord);
        tileColor.w=1.0;
        gl_FragColor = tileColor;
    }`,

    attributes: {
      position: [[0, 0], [1, 0], [0, 1], [0, 1], [1, 0], [1, 1]],
      aVertexTextureCoords: [[0, 1], [1, 1], [0, 0], [0, 0], [1, 1], [1, 0]]
    },

    uniforms: {
      //distance: regl.prop("distance"),
      projView: regl.prop("projView"),
      imageTXT: regl.prop("imageTXT"),
      //minViewportDimension: regl.prop("minViewportDimension"),
      //elapsed: ({ time }, { startTime = 0 }) => (time - startTime) * 1000,
    },

    count: 6,

    primitive: "triangle",

    blend: {
      enable: true,
      func: {
        srcRGB: "src alpha",
        srcAlpha: 1,
        dstRGB: 0,
        dstAlpha: "zero",
      },
    },
  });
}
