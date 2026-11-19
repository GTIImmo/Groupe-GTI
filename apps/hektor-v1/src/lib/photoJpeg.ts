// 19/11/2026 (étape 4 §89, D10) : une photo WebP devient un JPEG DANS LE NAVIGATEUR avant de partir (trombone de
// l'assistant, étape 2 de la fenêtre de création). Mesure du 19/11 : 62 travaux `upload_hektor_photo`, AUCUN en WebP --
// on ne parie pas sur l'accueil de Hektor, on lui envoie ce qu'il a toujours reçu.
// Tout autre fichier est rendu tel quel. Un échec de conversion rend le fichier d'origine : le refus éventuel reste
// celui d'aujourd'hui (la carte « Ajouter des photos » dira « pas une photo JPEG ou PNG »).

export async function webpEnJpeg(fichier: File, qualite = 0.92): Promise<File> {
  if (fichier.type !== 'image/webp') return fichier
  try {
    const image = await createImageBitmap(fichier)
    const toile = document.createElement('canvas')
    toile.width = image.width
    toile.height = image.height
    const ctx = toile.getContext('2d')
    if (!ctx) return fichier
    ctx.fillStyle = '#ffffff'  // le JPEG n'a pas de transparence : fond blanc plutôt que noir
    ctx.fillRect(0, 0, toile.width, toile.height)
    ctx.drawImage(image, 0, 0)
    image.close()
    const blob = await new Promise<Blob | null>((resoudre) => toile.toBlob(resoudre, 'image/jpeg', qualite))
    if (!blob) return fichier
    return new File([blob], `${fichier.name.replace(/\.webp$/i, '')}.jpg`, { type: 'image/jpeg', lastModified: fichier.lastModified })
  } catch {
    return fichier
  }
}
