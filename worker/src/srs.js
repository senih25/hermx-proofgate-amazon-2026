// Port of srs.py (SM-2). Keep the two in sync.
export const MIN_EF = 1.3;

function addDays(isoDay, days) {
  const d = new Date(isoDay + "T00:00:00Z");
  d.setUTCDate(d.getUTCDate() + days);
  return d.toISOString().slice(0, 10);
}

export function review(grade, repetitions, intervalDays, easiness, today) {
  if (!(grade >= 0 && grade <= 5)) throw new Error("GRADE_OUT_OF_RANGE");
  if (grade < 3) {
    repetitions = 0;
    intervalDays = 1;
  } else {
    if (repetitions === 0) intervalDays = 1;
    else if (repetitions === 1) intervalDays = 6;
    else intervalDays = Math.round(intervalDays * easiness);
    repetitions += 1;
  }
  easiness = easiness + (0.1 - (5 - grade) * (0.08 + (5 - grade) * 0.02));
  easiness = Math.max(MIN_EF, easiness);
  return {
    repetitions,
    intervalDays,
    easiness: Math.round(easiness * 10000) / 10000,
    due: addDays(today, intervalDays),
  };
}
