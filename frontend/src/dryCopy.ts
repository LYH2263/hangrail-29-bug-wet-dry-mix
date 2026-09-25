export function orderStateWord(raw: string | null): string {
  if (raw === "wet") return "湿衣";
  if (raw === "dry") return "干衣";
  return "干衣（历史未标注）";
}

export function pieceMark(raw: string | null): string {
  return raw === "wet" ? "湿" : "干";
}
