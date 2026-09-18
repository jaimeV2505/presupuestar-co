export default {
  content: ['./index.html','./src/**/*.{js,jsx}'],
  theme: { extend: {
    colors: {
      navy:  {50:'#EEF2F8',100:'#C9D7EC',200:'#9DB8DA',300:'#6A91C1',400:'#3D70A9',500:'#1C3A5E',600:'#162E4B',700:'#0F2136',800:'#091523',900:'#040A11'},
      steel: {400:'#3D92C3',500:'#2D6A9F',600:'#235480'},
    },
    fontFamily: { sans:['Inter','system-ui','sans-serif'], mono:['JetBrains Mono','monospace'] },
    borderRadius: { xl:'0.75rem', '2xl':'1rem', '3xl':'1.5rem' },
    keyframes: {
      fadeIn: { '0%': { opacity: '0', transform: 'translateY(-4px)' }, '100%': { opacity: '1', transform: 'translateY(0)' } },
      slideIn: { '0%': { opacity: '0', transform: 'translateX(16px)' }, '100%': { opacity: '1', transform: 'translateX(0)' } },
      popIn: { '0%': { opacity: '0', transform: 'scale(0.9) translateY(8px)' }, '60%': { opacity: '1', transform: 'scale(1.02) translateY(0)' }, '100%': { opacity: '1', transform: 'scale(1) translateY(0)' } },
      wave: { '0%,100%': { transform: 'rotate(0deg)' }, '20%': { transform: 'rotate(14deg)' }, '40%': { transform: 'rotate(-8deg)' }, '60%': { transform: 'rotate(14deg)' }, '80%': { transform: 'rotate(-4deg)' } },
    },
    animation: {
      fadeIn: 'fadeIn 0.3s ease-out',
      slideIn: 'slideIn 0.35s ease-out',
      popIn: 'popIn 0.45s cubic-bezier(0.34,1.56,0.64,1)',
      wave: 'wave 1.8s ease-in-out 1',
    },
  }},
  plugins:[]
}
