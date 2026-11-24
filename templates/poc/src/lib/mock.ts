/**
 * Mock-data layer pattern for MZtech PoCs.
 * No backend, no real users: typed fixtures + fake latency + localStorage.
 * Replace fixtures per project; keep the async API shape so swapping in a
 * real backend later is trivial.
 */

const LATENCY_MS = 220

/** Simulate network latency so loading states are visible in the demo. */
export function delay<T>(value: T, ms: number = LATENCY_MS): Promise<T> {
  return new Promise((resolve) => setTimeout(() => resolve(value), ms))
}

export function uid(prefix = 'id'): string {
  return `${prefix}_${Math.random().toString(36).slice(2, 9)}`
}

/** Load a persisted collection, falling back to fixtures on first run. */
export function loadStore<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(key)
    if (raw) return JSON.parse(raw) as T
  } catch {
    /* corrupted storage -> fall back to fixtures */
  }
  return structuredClone(fallback)
}

export function saveStore<T>(key: string, value: T): void {
  try {
    localStorage.setItem(key, JSON.stringify(value))
  } catch {
    /* storage full/blocked: demo keeps working in memory */
  }
}

export function clearStore(key: string): void {
  localStorage.removeItem(key)
}

/** ISO date (yyyy-mm-dd) for a day offset from today. */
export function dayISO(offset = 0): string {
  const d = new Date()
  d.setDate(d.getDate() + offset)
  return d.toISOString().slice(0, 10)
}

/** Monday of the week containing `date`. */
export function mondayOf(date: Date): Date {
  const d = new Date(date)
  const day = (d.getDay() + 6) % 7
  d.setDate(d.getDate() - day)
  d.setHours(0, 0, 0, 0)
  return d
}

export function addDays(date: Date, days: number): Date {
  const d = new Date(date)
  d.setDate(d.getDate() + days)
  return d
}

export function fmtDay(date: Date): string {
  return date.toLocaleDateString('es-ES', { weekday: 'short', day: 'numeric' })
}

export function fmtRange(startHour: number, endHour: number): string {
  return `${String(startHour).padStart(2, '0')}:00–${String(endHour).padStart(2, '0')}:00`
}

/** Half-open interval overlap test: [aStart,aEnd) vs [bStart,bEnd). */
export function overlaps(aStart: number, aEnd: number, bStart: number, bEnd: number): boolean {
  return aStart < bEnd && bStart < aEnd
}
