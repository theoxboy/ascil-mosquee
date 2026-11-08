// Vidéos des pages créées (étape M2) : lien YouTube, Vimeo ou Facebook -> adresse de lecture intégrée.
// Seuls ces trois sites sont acceptés ; YouTube est lu en mode « sans cookie » (youtube-nocookie.com)
// et Vimeo sans pistage (dnt=1).

export const VIDEO_HOSTS = ['https://www.youtube-nocookie.com', 'https://player.vimeo.com', 'https://www.facebook.com'];

export function parseVideo(raw) {
  let u;
  try { u = new URL(String(raw || '').trim()); } catch { return null; }
  if (u.protocol !== 'https:' && u.protocol !== 'http:') return null;
  const host = u.hostname.replace(/^(www\.|m\.)/, '').toLowerCase();
  const yt = (id) => (/^[A-Za-z0-9_-]{11}$/.test(id || '') ? { provider: 'YouTube', embed: `https://www.youtube-nocookie.com/embed/${id}` } : null);
  if (host === 'youtu.be') return yt(u.pathname.split('/')[1]);
  if (host === 'youtube.com' || host === 'youtube-nocookie.com' || host === 'music.youtube.com') {
    if (u.pathname === '/watch') return yt(u.searchParams.get('v'));
    const m = /^\/(?:embed|shorts|live|v)\/([^/?#]+)/.exec(u.pathname);
    return m ? yt(m[1]) : null;
  }
  if (host === 'vimeo.com' || host === 'player.vimeo.com') {
    const m = /\/(?:video\/)?(\d{5,12})(?:\/|$)/.exec(u.pathname);
    return m ? { provider: 'Vimeo', embed: `https://player.vimeo.com/video/${m[1]}?dnt=1` } : null;
  }
  if (host === 'facebook.com' || host === 'fb.watch') {
    if (host === 'facebook.com' && !/\/(videos|watch|reel)\b/.test(u.pathname + u.search)) return null;
    const clean = `https://${host === 'fb.watch' ? 'fb.watch' : 'www.facebook.com'}${u.pathname}${u.pathname === '/watch/' || u.pathname === '/watch' ? u.search : ''}`;
    return { provider: 'Facebook', embed: `https://www.facebook.com/plugins/video.php?href=${encodeURIComponent(clean)}&show_text=false` };
  }
  return null;
}
