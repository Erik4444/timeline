export const SOURCE_COLORS: Record<string, string> = {
  whatsapp: '#25D366',
  calendar: '#4285F4',
  photos: '#FF6B35',
  spotify: '#1DB954',
  instagram: '#E1306C',
  facebook: '#1877F2',
  telegram: '#2CA5E0',
  twitter: '#1DA1F2',
  google_takeout: '#DB4437',
  apple_health: '#FF2D55',
  netflix: '#E50914',
  default: '#8B5CF6',
};

export function getSourceColor(source: string): string {
  return SOURCE_COLORS[source] ?? SOURCE_COLORS.default;
}

export const SOURCE_LABELS: Record<string, string> = {
  whatsapp: 'WhatsApp',
  calendar: 'Kalender',
  photos: 'Fotos',
  spotify: 'Spotify',
  instagram: 'Instagram',
  facebook: 'Facebook',
  telegram: 'Telegram',
  twitter: 'Twitter',
  google_takeout: 'Google',
  apple_health: 'Apple Health',
  netflix: 'Netflix',
};

export function getSourceLabel(source: string): string {
  return SOURCE_LABELS[source] ?? source;
}

export const EVENT_TYPE_EMOJI: Record<string, string> = {
  message: '💬',
  calendar_event: '📅',
  photo: '📷',
  music_play: '🎵',
  post: '📝',
  story: '✨',
  location: '📍',
  default: '•',
};

export function getEventEmoji(eventType: string): string {
  return EVENT_TYPE_EMOJI[eventType] ?? EVENT_TYPE_EMOJI.default;
}
