import { CALIBRATION_FRAME_TARGET } from "../model/constants";

export class CalibrationBuffer {
  private values: number[] = [];

  add(value: number) {
    this.values.push(value);
  }

  get progress() {
    return Math.min(this.values.length / CALIBRATION_FRAME_TARGET, 1);
  }

  get isComplete() {
    return this.values.length >= CALIBRATION_FRAME_TARGET;
  }

  finalize(upRatio: number, downRatio: number) {
    if (!this.isComplete) {
      return null;
    }

    const baseline = this.values.reduce((total, value) => total + value, 0) / this.values.length;

    return {
      baseline,
      upThreshold: baseline * upRatio,
      downThreshold: baseline * downRatio,
    };
  }

  reset() {
    this.values = [];
  }
}
