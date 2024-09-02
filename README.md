# Overview: Creating Summaries from Large Databases

## Preface
As a rule, the study of any physical object targets creating its physical model, which means defining its main operation parameters. Once this group of parameters is defined, one can start determining the influence of each on the object's performance by separating strong, weak, and negligible parameters. In classical experimental physics, the usual procedure is to vary one parameter while fixing the others. Thus, for each study, we define one parameter as variable and measure the object's performance while keeping the rest non-variable. Then we define another parameter as variable and repeat the experiment until we reveal the true influence of each parameter.

## Description
This program processes organized experimental data, where each folder represents a different variable parameter (as defined above). It reads the data from Excel files, which consist of row-based database paired x and y values from a certain experiment. The program identifies key fixed parameters from the file names, performs calculations, and generates summary plots.

### Features:
- The program repeats each measurement multiple times, allowing for regression calculation as an average instead of classical analytical regression.
- Displays regression lines showing the average results for each test condition.
- Calculates how well the regression lines fit the data using the coefficient of determination (R²).
- Users can view, save, or further analyze the generated plots and data.

### R² Calculation Formulas:
R² = 1 - (SSres / SStot) SSres = Σ(y_reg - y_i)² SStot = Σ(y_i - y_mean)²

The program compares the actual test results (y_i) to the regression line (y_reg) to calculate R².

## What the Program Does
For each variable parameter:
- The program processes Excel-based x and y row databases of every experiment, considering corresponding fixed parameters.
  
- Example: In a dataset where the variable parameter is Cell Gap Height (e.g., 50 µm), fixed parameters are S11 and S12 both at 0 and 20V phase change, and T(fall) and T(rise).

- A regression line is created by averaging and calculating R² to show how closely the data points follow the regression line.

- Places all resulting lines on one graph.
  
- **Example:** The resulting regression lines for each variable parameter are displayed on a single graph, with the average R² between every experiment.

The program also provides an expanded list of R² calculations in the command prompt.

### Additional Functionality
Other than the default mode, the program can process phase change data to calculate response time specific to VNA testing. It receives Excel files and outputs a table containing response time and maximum phase.

## How to Use the Program

1. **Set Up Folder:**  
   Create a folder where the program will store your data. Upon launching the program, input the path to this folder.
   
2. **Add Test Data:**  
   Insert your Excel test data files into the folder. The first column should be x-data (e.g., frequency), and the second column should be y-data (e.g., logM).
   
3. **File Naming Convention:**  
   Name your files using underscores to separate each key parameter, as shown below:
   JNC_Heights_01-07-24_PhaseShifter_CellGap_50mkm_15r_S11_LOGM_0V_2024-07-02_12-47-17.xlsx
   The program will interpret this file name to identify the variables. For example, the Cell Gap and 50mkm will be set as the variable parameter and value, respectively. S11 and 0V will be set as fixed parameters, and 15r will be the experiment number.

4. **Launch Program:**  
This Python-based program requires the installation of libraries such as `pandas`, `matplotlib`, and `numpy`. You will be prompted to input the source folder and have options to perform setup, ignore first and second fixed variables, or cancel the difference plot drawings.

5. **View Results:**  
The program will display the plots, which can be saved manually. You can also copy additional R² values from the command prompt.

