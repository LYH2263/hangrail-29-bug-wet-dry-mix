export function orderStateWord(raw: string | null): string {
  if (raw == null) return "干衣（历史未标注）";
  if (raw === "wet") return "湿衣";
  return "干衣";
}

export function pieceMark(raw: string | null): string {
  if (raw === "wet") return "湿";
  return "干";
}
