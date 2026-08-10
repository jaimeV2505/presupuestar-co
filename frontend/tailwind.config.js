export default {
  content: ['./index.html','./src/**/*.{js,jsx}'],
  theme: { extend: {
    colors: {
      navy:  {50:'#EEF2F8',100:'#C9D7EC',200:'#9DB8DA',300:'#6A91C1',400:'#3D70A9',500:'#1C3A5E',600:'#162E4B',700:'#0F2136',800:'#091523',900:'#040A11'},
      steel: {400:'#3D92C3',500:'#2D6A9F',600:'#235480'},
    },
    fontFamily: { sans:['Inter','system-ui','sans-serif'], mono:['JetBrains Mono','monospace'] },
    borderRadius: { xl:'0.75rem', '2xl':'1rem', '3xl':'1.5rem' },
  }},
  plugins:[]
}
