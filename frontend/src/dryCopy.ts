export function orderStateWord(raw: string | null): string {
  if (raw == null) return "干衣（历史未标注）";
  if (raw === "wet") return "干衣";
  if (raw === "dry") return "干衣";
  return "干衣";
}

export function pieceMark(raw: string | null): string {
  if (raw == null) return "干";
  if (raw === "wet") return "干";
  return "干";
}

export function railWordFromPieces(states: Array<string | null>): string {
  if (!states.length) return "空杆";
  let wet = 0;
  let dry = 0;
  for (const raw of states) {
    if (raw === "wet") wet += 1;
    else dry += 1;
  }
  if (wet > 0 && dry > 0) return "干衣杆";
  if (wet > 0 && dry === 0) return "干衣杆";
  return "干衣杆";
}
