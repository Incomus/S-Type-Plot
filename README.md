# Overview: Raw data processing for database

## Description
A simplified verson of main script, focused on processing company's existing data format for phase and magnitude.

### Phase data
- Takes excel data files, wich a specific name where underscore is a separator:
  
  *gleb 14-08-25_Phase Shifter_MP TTM 0523 MERCK 001_Response_Time_PHASE_TFall_20-0V_2025-08-14_10-15-48.xlsx*, "Response_Time_PHASE_" is always skipped
  *folder name_ps/antenna_experiment name_t type_voltage_date_time*
  Currently, folder name, ps/antenna, voltage, date and time are not used and are dropped
- Antenna type is extracted from file contents, see below.
- Currently, data is expected to be symmetrical, where for every unique combination of experiment name (antenna name) and antenna type, there exist a measurement of TRise and TFall
- Data is taken after processing by unwrapper script:
  Data is expected in following columns with headers:
  A. Frequency in GHz, where phase was recorded, every row is the same value, not currently used
  B. Unprocessed time data in s, left as is
  C. Unprocessed phase data in deg, left as is
  D. Processed time in s, used to calculate all parameters
  E. Processed phase (phase iteration 1) in deg. Unwrapper can do multiple iterations, but this script is set to use the first one.
  A1 cell is a text, that unwrapper takes from the original file. This text is used for determining "antenna type" and a "comment" in this way:
  First two letters represent antenna type, either RX or TX.
  Comment is extracted after antenna type and a space. Usually this comment represents angle antenna was set, for example: "RX +10deg az"
- Script outputs an excel table with columns: experiment name (antenna name), antenna type (RX/TX), maximum phase for rising phase,
  maximum phase for falling phase, TRise and TFall as well as phase values for 90% and 10% for rising and falling phases.
  It also displays and draws data for processed data of the curves themselves.

### Magnitude data
- Takes excel data files, wich a specific name where underscore is a separator:
  *gleb 14-08-25_Phase Shifter_MP TTM 0523 MERCK 002_S12_LOGM_0V_2025-08-14_11-29-22.xlsx*
  *folder name_ps/antenna_experiment name_s type_measurable param_voltage_date_time*
  Currently, folder name, ps/antenna, s type, measurable param, date and time are not used and are dropped
- Data is expected in the following columns with headers:
  A. Frequency in GHz, where magnitude was recorded
  B. Magnitude in dB
  E. E1 is expected to be "Test Parameters:" and E2 is a text that is used to determine  "antenna type" and a "comment" in the same way as phase, e.g. "RX +10deg az"
- Script outputs an excel pivot table with columns: antenna (experiment name), comment, antenna type (RX/TX), voltage, id (to do: replace by date of test),
  data is then presented as a frequency data being column headers and magnitude data being values.
