import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Instructions for creating folder structure and adding test data
print("""
How to:
1. Create a folder with the parameter name you want to test.
2. Inside that folder, create subfolders for each variation of the parameter (e.g., gap with 50, 75, and 100 μm).
3. Place the WNA Excel test data for S11/S12 (logM) in the respective folders.
4. The program expects filenames in the following format, where each part is separated by an underscore:
   'JNC Heights 01-07-24_Phase Shifter_15 r_S11_LOGM_0V_2024-07-02_12-47-17'
   This format is interpreted as: name (not used), type (not used), experiment number, primary, measurable, secondary, date (not used), time (not used).
   
""")

# Path to the main folder containing parameter folders
while True:
    main_folder_path = input('Input path to the main folder:\n')  # e.g., r"C:\Users\amirh\Downloads\tests"
    try:
        variable_count = 0
        variable_param_count = 0
        experiment_count = 0
        os.listdir(main_folder_path)
        for param_name in os.listdir(main_folder_path):
            param_name_path = os.path.join(main_folder_path, param_name)
            variable_count += 1
            # Loop through each variation folder within the parameter folder
            for param_folder in os.listdir(param_name_path):
                variable_param_count += 1
                param_folder_path = os.path.join(param_name_path, param_folder)
                
                # Check if it is a folder
                if os.path.isdir(param_folder_path):
                    # List all .xlsx files in the parameter folder
                    files = [f for f in os.listdir(param_folder_path) if f.endswith('.xlsx')]
                    experiment_count += len(files)
        print(f'found {variable_count} variable parameters')
        print(f'found {variable_param_count} variable variations')
        print(f'found {experiment_count} experiments')
        break
    except Exception as e:
        print(f'{e}\n')
    
ignore_primary = None
ignore_secondary = None
ignore_diff = None

def choose_2(op_1, op_2, text):
    user_input = None
    while user_input not in [op_1, op_2]:
        user_input = input(f'{text} ({op_1}/{op_2})\n')
        if user_input not in [op_1, op_2]:
            print('Invalid input\n')
    return user_input        
            
user_input = choose_2('y', 'n', 'Enter setup?')

if user_input == 'y':
    ignore_primary = choose_2('y', 'n', 'Ignore first variable?')
    ignore_secondary = choose_2('y', 'n', 'Ignore second variable?')
    if ignore_secondary == 'n':
        ignore_diff = choose_2('y', 'n', 'Ignore difference?')

# Data storage lists
data = []
failed_files = []

# Loop through each parameter folder in the main folder
for param_name in os.listdir(main_folder_path):
    param_name_path = os.path.join(main_folder_path, param_name)

    # Loop through each variation folder within the parameter folder
    for param_folder in os.listdir(param_name_path):
        param_folder_path = os.path.join(param_name_path, param_folder)
        
        # Check if it is a folder
        if os.path.isdir(param_folder_path):
            # List all .xlsx files in the parameter folder
            files = [f for f in os.listdir(param_folder_path) if f.endswith('.xlsx')]
            
            for file in files:
                file_path = os.path.join(param_folder_path, file)
                # Extract variables from the file name
                file_name, _ = os.path.splitext(file)
                variables = file_name.split('_')
                
                # Create DataFrame for the variables
                df_vars = pd.DataFrame(columns=[f'variable{i+1}' for i in range(len(variables))])
                for i, var in enumerate(variables):
                    df_vars[f'variable{i+1}'] = [var]
                
                try:
                    # Read the Excel file
                    df = pd.read_excel(file_path)
                    df.columns = df.columns.str.lower().str.replace(" ", "_")
                    df = df[df.columns[:2]]
                    
                    # Add metadata to the DataFrame
                    for i in range(len(variables)):
                        df[f'variable{i+1}'] = variables[i]
                    df['main_parameter'] = param_folder
                    
                    # Append the DataFrame to the list
                    data.append(df)
                except Exception as e:
                    # Store the failed file path and error message
                    failed_files.append((file_path, str(e)))
                    continue

    # Combine all DataFrames into a single DataFrame
    if data:
        final_df = pd.concat(data, ignore_index=True)
        # Save or use final_df as needed
    else:
        print("No valid data found.")

    if failed_files:
        print("Files that did not pass:")
        for file_path, error_message in failed_files:
            print(f"{file_path}: {error_message}")
    
    # Process and clean the final DataFrame
    measurable = final_df.columns[1]
    values = final_df.columns[0]
    final_df.columns = ['frequency_[ghz]', 'logm', 'name', 'type', 'exp_n', 'primary', 'measurable', 'secondary', 'date', 'time', 'main_parameter']
    final_df.drop(columns=['name', 'type', 'measurable', 'date', 'time'], inplace=True)

    # Get unique primarys and secondarys
    if ignore_primary == 'y':
        final_df['primary'] = ''
    if ignore_secondary == 'y':
        final_df['secondary'] = ''
    unique_primarys = final_df['primary'].unique()
    unique_secondarys = final_df['secondary'].unique()
    
    # Calculating R2
    final_df['R2'] = None
    for primary in unique_primarys:
        for secondary in unique_secondarys:
            filtered_df = final_df[(final_df['primary'] == primary) & (final_df['secondary'] == secondary)]
            grouped = filtered_df.groupby(['main_parameter', 'primary', 'secondary', 'frequency_[ghz]'])['logm'].mean().reset_index()
            grouped.rename(columns={'logm': 'avg_logm'}, inplace=True)

            for exp in final_df['exp_n'].unique():
                exp_df = filtered_df[filtered_df['exp_n'] == exp].reset_index(drop=True)
                exp_avg = grouped[(grouped['primary'] == primary) & (grouped['secondary'] == secondary) & (grouped['main_parameter'] == exp_df['main_parameter'][0])].reset_index(drop=True)['avg_logm']
                exp_merged = exp_df.join(exp_avg)
                ss_res = (exp_merged['avg_logm'] - exp_merged['logm']) ** 2
                ss_tot = (exp_merged['logm'] - exp_merged['logm'].mean()) ** 2
                r2_value = 1 - ss_res.sum() / ss_tot.sum()

                final_df.loc[(final_df['primary'] == primary) & (final_df['secondary'] == secondary) & (final_df['exp_n'] == exp), 'R2'] = r2_value
    # Group by main parameters and plot the data
    grouped = final_df.groupby(['main_parameter', 'primary', 'secondary', 'frequency_[ghz]'])['logm'].mean().reset_index()
    grouped = grouped.rename(columns={'logm': 'avg_logm'})
    
    # Define the grid size for subplots based on the number of unique primary and secondary combinations
    n_rows = len(unique_primarys)
    n_cols = len(unique_secondarys) + 1
    if len(unique_secondarys) == 1:
        cols_1 = True
    else:
        cols_1 = False
        
    if n_rows == 1:
        n_rows += 1
        rows_1 = True
    else:
        rows_1 = False
    
    fig, axes = plt.subplots(nrows=n_rows, ncols=n_cols, figsize=(n_cols * 5, n_rows * 5))
    # Loop through combinations of primary and secondary to draw s/v plots
    for s_idx, primary in enumerate(unique_primarys):  # Loop over rows (unique_primarys)
        for v_idx, secondary in enumerate(unique_secondarys):  # Loop over columns (unique_secondarys)

            # Filter data for the current combination of primary and secondary
            filtered_df = grouped[(grouped['primary'] == primary) & (grouped['secondary'] == secondary)]
            
            # Get unique main_parameters
            main_parameters = filtered_df['main_parameter'].unique()
            
            # Plot for each main_parameter in the respective subplot
            #print(n_rows, n_cols)
            #print(s_idx, v_idx)
            #print(axes)
            ax = axes[s_idx, v_idx]  # Access the subplot in the column for the current secondary and row for primary
            param_legend = 'R2av:'
            for param in main_parameters:
                r2_mean = final_df.loc[
                    (final_df['primary'] == primary) & 
                    (final_df['secondary'] == secondary) & 
                    (final_df['main_parameter'] == param),
                    ['R2']
                ].mean()
                r2_mean = round(pd.to_numeric(r2_mean.values[0]), 3)
                param_legend += str(param) + '=' + str(r2_mean) + ';'
                param_df = filtered_df[filtered_df['main_parameter'] == param]
                ax.plot(param_df['frequency_[ghz]'], param_df['avg_logm'], label=f'{param}')
            
            # Set titles and labels for each subplot
            ax.set_xlabel(values)
            ax.set_ylabel(measurable)
            if ignore_primary != 'y' and ignore_secondary != 'y':
                legend_set = f'{primary}, {secondary}\n{param_legend}'
            elif ignore_primary != 'y':
                legend_set = f'{primary}\n{param_legend}'
            elif ignore_secondary != 'y':
                legend_set = f'{secondary}\n{param_legend}'
            else:
                legend_set = param_legend
            ax.set_title(legend_set, fontsize=8)
            ax.legend(title=param_name)
            ax.grid(True)
    
    # Plotting the secondary differences in the last column of each row
    if len(unique_secondarys) > 1 and ignore_diff != 'y':

        # Calculating the index for secondary difference column (last column in each row)
        secondary_diff = grouped.pivot_table(index=['main_parameter', 'primary', 'frequency_[ghz]'], columns='secondary', values='avg_logm')
        secondary_diff = secondary_diff.reset_index()
        secondary_diff['secondary_diff'] = secondary_diff[secondary_diff.columns[-len(unique_secondarys)]] - secondary_diff[secondary_diff.columns[-1]]

        for s_idx, primary in enumerate(unique_primarys):
            primary_df = secondary_diff[secondary_diff['primary'] == primary]
            ax = axes[s_idx, -1]  # Access the last column in the row
            
            for param in main_parameters:
                param_df = primary_df[primary_df['main_parameter'] == param]
                ax.plot(param_df['frequency_[ghz]'], param_df['secondary_diff'], label=f'{param}')
            
            # Set titles and labels for the secondary difference subplots
            ax.set_xlabel(values)
            ax.set_ylabel(measurable)
            if ignore_primary != 'y':
                legend_set = f'{primary}, {secondary_diff.columns[-len(unique_secondarys)-1]} - {secondary_diff.columns[-2]}'
            else:
                legend_set = f'{secondary_diff.columns[-len(unique_secondarys)-1]} - {secondary_diff.columns[-2]}'
            ax.set_title(legend_set)
            ax.legend(title=param_name)
            ax.grid(True)

    # Adjust layout so that subplots don't overlap
    plt.tight_layout()
    plt.subplots_adjust(wspace=0.15, hspace=0.35)
    
    # Display R² summary
    r2_summary = final_df.drop(columns=['frequency_[ghz]', 'logm']).drop_duplicates().reset_index(drop=True)
    r2_summary['R2'] = pd.to_numeric(r2_summary['R2'], errors='coerce')
    r2_summary['R2'] = round(r2_summary['R2'], 3)
    r2_summary = r2_summary.sort_values(by=['primary', 'secondary', 'main_parameter', 'exp_n']).reset_index(drop=True)
    print('\nMain parameter: ' + param_name)
    print(r2_summary)
    print()

    # Display the figure
    if rows_1:
        for ax in axes[-1, :]:
            ax.remove() 
    if cols_1:
        if rows_1:
            axes[0][-1].remove()
        else:
            for ax in axes[:, -1]:
                ax.remove() 
    else:
        if ignore_diff == 'y':
            if rows_1:
                axes[0][-1].remove()
            else:
                for ax in axes[:, -1]:
                    ax.remove() 
            
    plt.show()
input('Press Enter to exit\n')
