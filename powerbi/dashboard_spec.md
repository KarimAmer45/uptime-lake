# Equipment Health — report specification

Canvas: 1440 × 810, 16:9. Background `#08111F`; cards `#111C2E`; primary text `#F4F7FB`.

- Header: “Metro APU Equipment Health” and selected date range.
- Row 1: cards for Telemetry Coverage %, Anomaly Rate %, Peak Oil Temperature °C, and Health Status.
- Row 2 (left, 65% width): line chart by `calendar_date`; values `avg_oil_temperature_c` and
  `avg_motor_current_a`. Add failure-window readings as red columns on a secondary axis.
- Row 2 (right): gauge for Anomaly Rate % with 3% watch and 10% critical thresholds.
- Row 3 (left): line chart for `avg_tp2_bar`, `avg_tp3_bar`, and `avg_reservoirs_bar`.
- Row 3 (right): matrix by month with readings, coverage, anomalies, and failure-window readings.
- Slicers: date, month, equipment name. Use accessible alt text on every visual.

Do not label the explainable threshold flag as a prediction. It is an operational anomaly indicator aligned
to known failure windows, not a trained ML model.

