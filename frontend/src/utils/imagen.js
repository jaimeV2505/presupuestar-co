// Compresion de imagenes en el cliente antes de subir.
// Una foto de celular (3-8 MB) queda en ~60-120 KB sin perdida visible en pantalla.
// Aplaza el limite de la BD por anos y hace la app 5x mas rapida en redes lentas.
export function comprimirImagen(file, maxDim = 1280, calidad = 0.72) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onerror = () => reject(new Error('No se pudo leer la imagen'))
    reader.onload = () => {
      const img = new Image()
      img.onerror = () => reject(new Error('Archivo de imagen no valido'))
      img.onload = () => {
        let { width, height } = img
        if (width > maxDim || height > maxDim) {
          const escala = maxDim / Math.max(width, height)
          width = Math.round(width * escala)
          height = Math.round(height * escala)
        }
        const canvas = document.createElement('canvas')
        canvas.width = width
        canvas.height = height
        const ctx = canvas.getContext('2d')
        ctx.fillStyle = '#ffffff'          // fondo blanco (JPEG no tiene transparencia)
        ctx.fillRect(0, 0, width, height)
        ctx.drawImage(img, 0, 0, width, height)
        resolve(canvas.toDataURL('image/jpeg', calidad))
      }
      img.src = reader.result
    }
    reader.readAsDataURL(file)
  })
}
