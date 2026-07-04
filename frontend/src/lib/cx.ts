// Tiny className combiner (avoids a clsx dependency).
export function cx(...parts: Array<string | false | null | undefined>): string {
  return parts.filter(Boolean).join(' ');
}
