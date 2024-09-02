# Overview: Creating Summaries from Large Databases

## Preface
As a rule, study of any physical object has a target of creating its physical model, which means defining its main operation parameters. After this group of parameters is defined, one can start determining the influence of each of them on an object's performance, separating strong, weak and negligible parameters. In classical experimental physics, the usual procedure of parameter influence determination is varying one parameter while the rest of parameters from the group are fixed. Therefore, for each study we define any one parameter as variable and measure object performance when the rest are non-variable. Then we define other parameter as variable and repeat this experiment until we reveal real influence of each parameter.

## Description
This program processes organized experimental data, where each folder represents a different variable parameter (see its definition in preface above). It reads the data from Excel files, consisting of row database paired x and y values of a certain experiment, identifies key fixed parameters from the file names, performs calculations, and generates summary plots.

Since in this type of test we repeat each measurement a few times, it is possible to determine regression here as average instead of classical analytical regression. Program displays regression lines showing the average results for each test condition and calculates how well these lines fit the data using coefficient of determination (R²). The user can view, save, or further analyze the generated plots and data.

R² is calculated using following formulas

R² = 1 - (SSres / SStot) 

SSres = Σ(y_reg - y_i)² 

SStot = Σ(y_i - y_mean)²

The program compares the actual test results (y_i) to the regression line (y_reg) to calculate R².

### TLDR:
- The program repeats each measurement multiple times, allowing for regression calculation as an average instead of classical analytical regression.
- Displays regression lines showing the average results for each test condition.
- Calculates how well the regression lines fit the data using the coefficient of determination (R²).
- Users can view, save, or further analyze the generated plots and data.

## What the Program Does
- For every variable parameter, the program takes Excel-based x and y row database of every experiment with corresponding fixed parameters.
  ![image](https://github.com/user-attachments/assets/34d2b7a6-58fc-41d6-8dc4-0dcd712fbab0)
  Fig. 1 Example of row data containing thousands of measured points. Variable parameter for this database is Cell Gap Height (in this example it is 50 mkm), fixed parameters are S11 and S12, both at 0 and 20V, phase change and T(fall) and T(rise).
- Creates a regression line by taking an average and calculates coefficient of determination to shows how close the data points are to the regression line.
  ![image](https://github.com/user-attachments/assets/8dffc432-cdc8-4c0f-8e0e-0a36d530a423)
  Fig. 2 Regression line is calculated as an average of the experiments. Then, R² is calculated from a difference between it and other experiments
- Places all resulting lines on one graph.
  ![image](https://github.com/user-attachments/assets/4d3fc696-37b1-4448-8599-9ca91b469f35)
  Fig. 3 First part of final plot. Resulting regression lines for every variable parameter are drawn on a single graph with average R² between every experiment.
- Full list of R²'s can be viewed in command prompt
  ![image](https://github.com/user-attachments/assets/8e3db58e-61d5-4076-bf39-8b344f44b09a)
- Currently, the program takes two fixed parameters.
- First parameter can be numerical or categorical.
- Second parameter should be numerical.
- Additionally, for every first parameter, program plots a difference between regression lines of lowest and highest second parameters.
  ![image](https://github.com/user-attachments/assets/c862f39b-bcd5-4650-9869-749d0469229e)
  Fig. 5 Second part of final plot, calculated difference between regression lines
### Additional Functionality
Other than default mode of operation, there may exist other ways program can processes data. Currently, it has an additional function to process phase change data to calculate response time, specific for VNA testing. That mode of operation receives Excel files and outputs a table, containing response time and maximum phase.

## How to Use the Program

1. **Set Up Folder:**  
   First, create a folder where the program can store your data. After starting the program, you will be asked to input path to this folder.
   
2. **Add Test Data:**  
   Put your Excel test data files inside the folder. The first column should be your x-data (e.g., frequency), and the second should be your y-data (e.g., logM).
   
3. **File Naming Convention:**  
   Name your files using underscores to separate each key parameter, as shown below:
   JNC Heights 01-07-24_Phase Shifter_**Cell Gap_50mkm_15r_S11**_LOGM_**0V**_2024-07-02_12-47-17.xlsx
   The program will interpret this file name to identify the variables: positions of Cell Gap and 50mkm will be set as variable parameter name and value respectively, S11 and 0V will be set as fixed parameters, 15r will be set as experiment number.

4. **Launch Program:**  
   This program operates in Python code language and will require you to install this language as well as all required libraries: pandas, matplotlib and numpy. You will be prompted to input source folder as well as given an option to perform setup. You can set a program to ignore first and second fixed variables or cancel drawing of difference plots.

5. **View Results:**  
   The program will display the plots, and you can save them manually. You can also copy extra R² values from the command prompt.

