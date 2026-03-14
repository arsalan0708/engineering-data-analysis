Engineering Data Analysis Tool
Structural engineers analyze large simulation datasets. This tool reads CSV files, finds peak stress/load values, and generates stress vs time charts.

Features
Import CSV dataset
Detect peak stress values
Summarize min/max/mean/p95 statistics
Plot stress vs time graphs
Multi-sensor plotting (comma-separated stress columns)
Direct value entry (CLI or interactive)
Requirements
Python 3.9+
Pandas
Matplotlib
Install
pip install -r requirements.txt
Usage
python analysis_tool.py --input data/sample.csv --time-col time --stress-col stress --output charts/stress_vs_time.png
Multi-sensor example:

python analysis_tool.py --input data/sample.csv --time-col time --stress-col stress,stress_sensor_b --output charts/stress_vs_time.png
Direct values (single series):

python analysis_tool.py --values 12.4,14.1,15.6,13.2,16.8,15.9 --time-values 0,1,2,3,4,5 --stress-col stress
Direct values (multi-sensor):

python analysis_tool.py --stress-col stress,stress_sensor_b --values "12.4,14.1,15.6;11.8,13.5,14.2" --time-values 0,1,2
Interactive prompt:

python analysis_tool.py --interactive --stress-col stress
Parameters
--input: Path to the CSV file
--time-col: Column name for time (default: time)
--stress-col: Column name(s) for stress/load, comma-separated (default: stress)
--values: Comma-separated stress values. For multiple stress columns, separate series with ;
--time-values: Comma-separated time values (optional)
--interactive: Prompt for values instead of reading a CSV
--output: Path to save the chart image (default: charts/stress_vs_time.png)
Output
Prints peak stress per column with its time
Prints summary stats per column (min/max/mean/p95/count)
Saves a PNG chart to the output path
