import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime
import traceback
import re
from openpyxl import Workbook, load_workbook
from openpyxl.chart import ScatterChart, Reference, Series
from openpyxl.chart.axis import ChartLines
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.drawing.image import Image
import numpy as np
from scipy.ndimage import gaussian_filter1d
sigma = 2

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
plt.rcParams['axes.prop_cycle'] = plt.cycler(color=['#ff7f0e',  # orange
                                                     '#2ca02c',  # green
                                                     '#1f77b4',  # blue
                                                     '#d62728',  # red
                                                     '#9467bd',  # purple
                                                     '#8c564b',  # brown
                                                     '#e377c2',  # pink
                                                     '#7f7f7f',  # gray
                                                     '#bcbd22',  # yellow-green
                                                     '#17becf']) # cyan
def collect_experiments(main_folder, depth):
    file_list = []
    
    def recursive_search(folder, current_depth, experiment_count):
        # Count Excel files in the current folder
        experiment_count += sum(1 for _ in folder.glob("*.xlsx"))
        for file in folder.glob("*.xlsx"):
            file_list.append(file)
        
        # Check if we can go deeper
        if depth == -1 or current_depth < depth:
            for subfolder in folder.iterdir():
                if subfolder.is_dir():
                    # Recursively search in the subfolder
                    experiment_count = recursive_search(subfolder, current_depth + 1, experiment_count)

        return experiment_count

    # Start the recursive search from the main folder
    experiment_count = recursive_search(main_folder, 0, 0)

    return experiment_count, file_list
    
def summarize_folders():
    while True:
        main_folder_path = input("Input path to the main folder:\n")
        main_folder = Path(main_folder_path)
        if main_folder.exists() and main_folder.is_dir():  # Check if the path exists and is a directory
            break  # Break the loop if the input is valid
        else:
            print(f"'{main_folder_path}' is not a valid directory. Please try again.")
    experiment_count, file_list = collect_experiments(main_folder, 5)
    print(f'Found {experiment_count} experiments')
    input('Press Enter to continue\n')
    return main_folder_path

def choose(text, *options):
    options = list(options)  # Convert the tuple to a list for easier handling
    if isinstance(options, list) and all(isinstance(item, list) for item in options):
        options = options[0]
    while (user_input := input(f'{text}\n({"/".join(options)})\n')) not in options:
        print('Invalid input\n')
    return user_input
    
def get_user_setup():
    def_state = choose('Choose operation:\n1 - Default/Magnitude\n2 - Phase response time', '1', '2')
    
    if choose('Change default settings?', 'y', 'n') == 'y':
        type = choose('Set data processing type:', '0', '1')
        type = int(type)
        ignore_primary = choose('Ignore first variable?', 'y', 'n') if def_state == '1' else 'n'
        ignore_secondary = choose('Ignore second variable?', 'y', 'n') if def_state == '1' else 'n'
        if def_state == '1':
            ignore_diff = choose('Ignore difference?', 'y', 'n') if ignore_secondary == 'n' else 'y'
        else:
            ignore_diff = 'n'
    else:
        def_state, type, ignore_primary, ignore_secondary, ignore_diff = def_state, '0', 'n', 'n', 'n'
    return def_state, type, ignore_primary, ignore_secondary, ignore_diff

def integ_mean(filtered_df, type=0):
    if type == 1:
        low_range = filtered_df['0'] < 11.666
        mid_range = (filtered_df['0'] > 11.666) & (filtered_df['0'] < 13.333)
        high_range = ~low_range & ~mid_range  # The rest
    else:
        low_range = filtered_df['x'] < 11.666
        mid_range = (filtered_df['x'] > 11.666) & (filtered_df['x'] < 13.333)
        high_range = ~low_range & ~mid_range  # The rest
    main_parameters = filtered_df['main_parameter'].unique()
    xes = filtered_df['x'].unique()
    words = ['avg_y', 'y']
    for word in words:
        try:
            for param in main_parameters:
                if type == 1:
                    for x in xes:
                        # Calculate mean for each range
                        low_mean = filtered_df.loc[(low_range) & (filtered_df['main_parameter'] == param) & (filtered_df['x'] == x), word].mean()
                        mid_mean = filtered_df.loc[(mid_range) & (filtered_df['main_parameter'] == param) & (filtered_df['x'] == x), word].mean()
                        high_mean = filtered_df.loc[(high_range) & (filtered_df['main_parameter'] == param) & (filtered_df['x'] == x), word].mean()

                         # Replace y values in the original DataFrame
                        filtered_df.loc[(low_range) & (filtered_df['main_parameter'] == param) & (filtered_df['x'] == x), word] = low_mean
                        filtered_df.loc[(mid_range) & (filtered_df['main_parameter'] == param) & (filtered_df['x'] == x), word] = mid_mean
                        filtered_df.loc[(high_range) & (filtered_df['main_parameter'] == param) & (filtered_df['x'] == x), word] = high_mean
                else:
                    # Calculate mean for each range
                    low_mean = filtered_df.loc[(low_range) & (filtered_df['main_parameter'] == param), word].mean()
                    mid_mean = filtered_df.loc[(mid_range) & (filtered_df['main_parameter'] == param), word].mean()
                    high_mean = filtered_df.loc[(high_range) & (filtered_df['main_parameter'] == param), word].mean()

                     # Replace y values in the original DataFrame
                    filtered_df.loc[(low_range) & (filtered_df['main_parameter'] == param), word] = low_mean
                    filtered_df.loc[(mid_range) & (filtered_df['main_parameter'] == param), word] = mid_mean
                    filtered_df.loc[(high_range) & (filtered_df['main_parameter'] == param), word] = high_mean
        except:
            None
    if type == 1:
        new_df = pd.DataFrame()
        for param in main_parameters:
            for x in xes:
                temp_df = filtered_df.loc[(filtered_df['main_parameter'] == param) & (filtered_df['x'] == x)].reset_index(drop=True)
                temp_df = temp_df.iloc[[int(len(temp_df)/2)]]
                new_df = pd.concat([new_df, temp_df], ignore_index=True)
        return new_df
    return filtered_df

def rename_col(df):
    while True:
        columns_df = pd.DataFrame({
            'Column Name': df.columns,
            'Column Data': [df[col].iloc[0] for col in df.columns]
        })
        print(columns_df)
        range_list = [str(i) for i in range(len(df.columns))]
        flip_1 = choose('What column to flip 1', range_list)
        flip_1 = df.columns[int(flip_1)]
        flip_2 = choose('What column to flip 2', range_list)
        flip_2 = df.columns[int(flip_2)]
        df = df.rename(columns={flip_1: 'temp', flip_2: flip_1})
        df = df.rename(columns={'temp': flip_2})
        keep = choose('Continue?', 'y', 'n')
        if keep == 'n':
            return df

def custom_sort_key(s):
    return [int(text) if text.isdigit() else text for text in re.findall(r'\d+|\D+', s)]

def interpolate(xi, yi, xj, yj):
    def interpol(x_long, y_long, x_shor, y_shor):
        interpolated_x = []
        interpolated_y = []
        dx_long = round(x_long[1] - x_long[0], 3)
        for i in range(len(x_shor)-1):
            x_vals = np.arange(x_shor[i], x_shor[i + 1], dx_long)
            y_vals = np.linspace(y_shor[i], y_shor[i + 1], len(x_vals))
            interpolated_x.extend(x_vals)
            interpolated_y.extend(y_vals)
        interpolated_x = np.array(interpolated_x)
        interpolated_y = np.array(interpolated_y)
        return interpolated_x, interpolated_y
    if len(xi)!= len(xj):
        if len(xi) > len(xj):
            xj, yj = interpol(xi, yi, xj, yj)
        else:
            xi, yi = interpol(xj, yj, xi, yi)
    return xi, yi, xj, yj

def process_files(main_folder_path, def_state):
    data, failed_files = [], []
    main_folder = Path(main_folder_path)
    experiment_count, file_list = collect_experiments(main_folder, 5)
    count = 0
    first_columns = None
    for file in file_list:
        try:
            df = pd.read_excel(file)
            file = file.stem
            file = file.replace("_Gleb_", " Gleb ")
            if def_state == '2':
                file = file.replace("Response_Time", "Response Time").replace("TFall_", "TFall ").replace("TRise_", "TRise ")
                df = df.iloc[:, 1:3]
            else:
                file = file
                df = df.iloc[:, :2]  # Keep only first two columns
            
            if first_columns is None:
                first_columns = df.columns.tolist()
            else:
                # Rename the columns of the current file to match the first file
                df.columns = first_columns
            
            variables = file.split('_')
            for i, var in enumerate(variables):
                df[f'variable{i+1}'] = var

            df['id'] = count
            count += 1
            data.append(df)
        except Exception as e:
            print(e)
            failed_files.append((file, str(e)))

    if data:
        df = pd.concat(data, ignore_index=True)
    else:
        print("No valid data found.")
        return pd.DataFrame(), failed_files
    
    return df, failed_files

def preprocess(df, type, def_state, ignore_primary, ignore_secondary):
    df.columns = df.columns.str.lower().str.replace(" ", "_")
    #if type == 1:
    #    df.columns = ['Cell Gap', 'Avg logM']
    #else:
    #    df.columns = ['Frequency [GHz]', 'logM']
    
    measurable = df.columns[1]
    values = df.columns[0]
    if def_state == '1':
        df.columns = ['x', 'y', 'name', 'type', 'param_name', 'main_parameter', 'exp_n', 'primary', 'measurable', 'secondary', 'date', 'time', 'id']
    else:
        cols = ['x', 'y', 'name', 'type', 'exp_n', 'main_parameter', 'primary', 'measurable', 'secondary', 'date', 'time', 'id']
        if len(df.columns) < len(cols):
            cols.remove('main_parameter')
            df.columns = cols
            df['main_parameter'] = ''
            df['param_name'] = ''
        else:
            df.columns = cols
            df['param_name'] = 'Cell Gap'
    df.drop(columns=['name', 'type', 'measurable', 'date', 'time'], inplace=True)
    
    
    df['0'] = 0
    if type == '1':
        df = rename_col(df)
        df['x'] = df['x'].astype(str).str.replace(r'[^\d.]', '', regex=True)  # Keep only numbers
        df['x'] = pd.to_numeric(df['x'], errors='coerce')  # Convert to numeric

    


    if df['main_parameter'].astype(str).str.contains('mkm').any():
        df['main_parameter'] = (
            df['main_parameter']
            .str.replace('mkm', 'um')         # Replace "mkm" with "um"
            .str.zfill(5)                     # Pad to ensure 3 digits for numbers
        )
    if df['param_name'].astype(str).str.contains('mkm').any():
        df['param_name'] = (
            df['param_name']
            .str.replace('mkm', 'um')         # Replace "mkm" with "um"
            .str.zfill(5)                     # Pad to ensure 3 digits for numbers
        )
        
    if ignore_primary == 'y':
        df['primary'] = ''
    if ignore_secondary == 'y':
        df['secondary'] = ''
    return df, measurable, values
    
def calculate_r2(final_df, ignore_primary, ignore_secondary, ignore_diff):
    if final_df.empty:
        return
    
    unique_params = final_df['main_parameter'].unique()
    unique_primarys = final_df['primary'].unique()
    unique_secondarys = final_df['secondary'].unique()

    final_df['R2'] = None
    final_df['avg_y'] = None
    for main_parameter in unique_params:
        for primary in unique_primarys:
            for secondary in unique_secondarys:
                filtered_df = final_df[(final_df['primary'] == primary) & (final_df['secondary'] == secondary) & (final_df['main_parameter'] == main_parameter)]
                grouped = filtered_df.groupby(['param_name', 'main_parameter', 'primary', 'secondary', 'x', '0'])['y'].mean().reset_index()
                grouped.rename(columns={'y': 'avg'}, inplace=True)

                for id in filtered_df['id'].unique():
                    exp_df = filtered_df[filtered_df['id'] == id].reset_index(drop=True)

                    # Merge exp_df with grouped by matching on 'param_name' and 'x'
                    exp_merged = pd.merge(exp_df, grouped, on=['param_name', 'main_parameter', 'primary', 'secondary', 'x'], how='left')

                    # Calculate SS_res and SS_tot
                    ss_res = (exp_merged['avg'] - exp_merged['y']) ** 2
                    ss_tot = (exp_merged['y'] - exp_merged['y'].mean()) ** 2
                    # Calculate R² value
                    r2_value = 1 - ss_res.sum() / ss_tot.sum()
                    
                    # Update final_df with the R² value
                    final_df.loc[(final_df['primary'] == primary) & (final_df['secondary'] == secondary) & 
                                 (final_df['id'] == id) & (final_df['main_parameter'] == main_parameter), 'R2'] = r2_value
                    final_df.loc[(final_df['primary'] == primary) & (final_df['secondary'] == secondary) & 
                                 (final_df['id'] == id) & (final_df['main_parameter'] == main_parameter), 'avg_y'] = exp_merged['y'].mean()
    return final_df
           
def process_data(df, def_state, type):
    if def_state == '1':
        unique_primarys = df['primary'].unique()
        unique_secondarys = df['secondary'].unique()
        new_df = pd.DataFrame()
        for param_name in df['param_name'].unique():
            filtered_df = df[df['param_name'] == param_name].reset_index(drop=True)
            grouped_df = filtered_df.groupby(['param_name', 'main_parameter', 'primary', 'secondary', 'x', '0'])['y'].mean().reset_index()
            grouped_df = grouped_df.rename(columns={'y': 'avg_y'})
            for s_idx, primary in enumerate(unique_primarys):  # Loop over rows (unique_primarys)
                for v_idx, secondary in enumerate(unique_secondarys):  # Loop over columns (unique_secondarys)

                    # Filter data for the current combination of primary and secondary
                    temp_df = grouped_df[(grouped_df['primary'] == primary) & (grouped_df['secondary'] == secondary)]
                    
                    
                    if type in [1]:
                        temp_df = integ_mean(temp_df, type)                                       #Integrated mean
                    #temp_df['avg_y'] = gaussian_filter1d(temp_df['avg_y'], sigma=sigma)                      #gaussian filter
                    #temp_df['avg_y'] = filtered_df['avg_y'].rolling(window=20, center=True).mean()               #rolling avg filter
                    new_df = pd.concat([new_df, temp_df], ignore_index=True)
        return new_df
    elif def_state == '2':
        return df
    
def final_plot(final_df, measurable, values, wb, type):
    r2 = False
    unique_primarys = final_df['primary'].unique()
    unique_secondarys = final_df['secondary'].unique()
    param_name = final_df['param_name'].iloc[0]
    param_name = str(param_name)
    
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
            filtered_df = final_df[(final_df['primary'] == primary) & (final_df['secondary'] == secondary)]
            # Get unique main_parameters
            main_parameters = filtered_df['main_parameter'].unique()

            sheet_name = f"{param_name}_{primary}_{secondary}"
            ws = wb.create_sheet(title=sheet_name)
            
            filtered_df.loc[:, 'avg_y'] = -filtered_df['avg_y']
            for row in dataframe_to_rows(filtered_df[['main_parameter', 'x', 'avg_y']], index=False, header=True):
                ws.append(row)
            filtered_df.loc[:, 'avg_y'] = -filtered_df['avg_y']

            # Create a line chart
            chart = ScatterChart()
            if type == 1:
                chart.x_axis.title = "Cell Gap"
                chart.y_axis.title = "Avg logM"
            else:
                chart.x_axis.title = "Frequency [GHz]"
                chart.y_axis.title = "logM"
                
            chart.title = "Main Parameter Line Chart"
            
            chart.x_axis.scaling.min = round(filtered_df['x'].min())
            chart.y_axis.scaling.min = round(-filtered_df['avg_y'].max())-1
            chart.x_axis.scaling.max = round(filtered_df['x'].max())
            chart.y_axis.scaling.max = round(-filtered_df['avg_y'].min())+1
            
            chart.x_axis.majorGridlines = ChartLines()
            chart.y_axis.majorGridlines = ChartLines()
            chart.x_axis.delete = False
            chart.y_axis.delete = False
            try:
                main_parameters = sorted(main_parameters, key=custom_sort_key)
            except:
                None

            # Loop through each unique main_parameter and add a series to the chart
            for param in main_parameters:
                # Filter rows matching the current main_parameter
                param_rows = [i + 2 for i, val in enumerate(filtered_df['main_parameter']) if val == param]
                min_row, max_row = min(param_rows), max(param_rows)

                # Set x and y data for each main_parameter
                x_data = Reference(ws, min_col=2, min_row=min_row, max_row=max_row)
                y_data = Reference(ws, min_col=3, min_row=min_row, max_row=max_row)
                series = Series(y_data, xvalues=x_data, title=param)
                series.smooth = False
                chart.series.append(series)

            # Place the chart below the data table
            ws.add_chart(chart, "E1")

            
            
            
            
            

            # Sorting the data based on custom sort key
            # Plot for each main_parameter in the respective subplot
            #print(n_rows, n_cols)
            #print(s_idx, v_idx)
            #print(axes)
            ax = axes[s_idx, v_idx]  # Access the subplot in the column for the current secondary and row for primary
            ax.xaxis.set_label_coords(0.5, -0.1)
            ax.yaxis.set_label_coords(-0.1, 0.5)
            if r2:
                param_legend = 'R2av:'
            for param in main_parameters:
                if r2:
                    r2_mean = final_df.loc[
                        (final_df['primary'] == primary) & 
                        (final_df['secondary'] == secondary) & 
                        (final_df['main_parameter'] == param),
                        ['R2']
                    ].mean()
                    r2_mean = pd.to_numeric(r2_mean.values[0])
                    param_legend += str(param) + '=' + f"{r2_mean:.2f}" + ';'
                else:
                    param_legend = ''
                param_df = filtered_df[filtered_df['main_parameter'] == param]
                ax.plot(param_df['x'], -param_df['avg_y'], label=f'{param}')
            # THIS SHIT HAS NOT BEEN APPROVED BY VATICAN THIS SHIT HAS NOT BEEN APPROVED BY VATICAN THIS SHIT HAS NOT BEEN APPROVED BY VATICAN
            #pivot_df = filtered_df.pivot(columns='main_parameter', values=['x', 'avg_y'])
            #xi, yi, xj, yj = interpolate(pivot_df[pivot_df.columns[0]].dropna().reset_index(drop=True), 
            #pivot_df[pivot_df.columns[2]].dropna().reset_index(drop=True), pivot_df[pivot_df.columns[1]].dropna().reset_index(drop=True), pivot_df[pivot_df.columns[3]].dropna().reset_index(drop=True))
            #pivot_df = pivot_df[:200]
            #pivot_df[pivot_df.columns[1]] = xj[:200]
            #pivot_df[pivot_df.columns[3]] = yj[:200]
            #pivot_df = pivot_df[[pivot_df.columns[2], pivot_df.columns[3]]]
            #corr = round(pivot_df.corr().loc[("avg_y", "Experiment"), ("avg_y", "Simulation")], 3)
            # THIS SHIT HAS NOT BEEN APPROVED BY VATICAN THIS SHIT HAS NOT BEEN APPROVED BY VATICAN THIS SHIT HAS NOT BEEN APPROVED BY VATICAN
            
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
            #legend_set += 'corr:' + str(corr) # THIS SHIT HAS NOT BEEN APPROVED BY VATICAN THIS SHIT HAS NOT BEEN APPROVED BY VATICAN THIS SHIT HAS NOT BEEN APPROVED BY VATICAN
            ax.set_title(legend_set, fontsize=8)
            ax.legend(title=param_name)
            ax.grid(True)
    
    # Plotting the secondary differences in the last column of each row
    if len(unique_secondarys) > 1 and ignore_diff != 'y':
        # Calculating the index for secondary difference column (last column in each row)
        secondary_diff = final_df.pivot_table(index=['main_parameter', 'primary', 'x'], columns='secondary', values='avg_y')
        secondary_diff = secondary_diff.reset_index()
        secondary_diff['secondary_diff'] = secondary_diff[secondary_diff.columns[-len(unique_secondarys)]] - secondary_diff[secondary_diff.columns[-1]]

        for s_idx, primary in enumerate(unique_primarys):
            primary_df = secondary_diff[secondary_diff['primary'] == primary]
            ax = axes[s_idx, -1]  # Access the last column in the row
            ax.xaxis.set_label_coords(0.5, -0.1)
            ax.yaxis.set_label_coords(-0.1, 0.5)
            
            for param in main_parameters:
                param_df = primary_df[primary_df['main_parameter'] == param]
                ax.plot(param_df['x'], -param_df['secondary_diff'], label=f'{param}')
            
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
    if r2:
        r2_summary = final_df.drop(columns=['x', 'y']).drop_duplicates().reset_index(drop=True)
        r2_summary['R2'] = pd.to_numeric(r2_summary['R2'], errors='coerce')
        r2_summary['R2'] = r2_summary['R2'].apply(lambda x: f"{x:.2f}")
        r2_summary['avg_y'] = r2_summary['avg_y'].apply(lambda x: f"{x:.2f}")
        final_df = final_df.rename(columns={'avg_y': f'avg_{measurable}'})
        r2_summary = r2_summary.sort_values(by=['main_parameter', 'primary', 'secondary', 'exp_n']).reset_index(drop=True)
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
            
    #plt.show()
    plt.savefig(f"{param_name}.jpeg", format='jpeg', dpi=300)
    plt.close()
        
def calculate_t(df, type):
    if df.empty:
        return
    if type == 1:
        new_df = pd.DataFrame()
        sheet_ids = []
        sheets = []
        sheet_names = []
        t_falls = []
        phases = []
        for id in df['id'].unique():
            filtered_df = df[df['id'] == id].reset_index(drop=True)
            filtered_df['dy'] = filtered_df['y'].diff()
            dy_max = filtered_df['dy'].abs().idxmax()
            print(dy_max)
            window_size = 8
            dy_max_minus = dy_max - window_size
            dy_max_plus = dy_max + window_size
            dy_max = int(round( filtered_df.iloc[dy_max_minus:dy_max_plus]
                                             .sort_values(by=['dy'])
                                             .head(6)
                                             .reset_index()['index']
                                             .mean() ))
            print(dy_max)
            k = filtered_df['dy'].iloc[dy_max] / ( filtered_df['x'].iloc[dy_max] - filtered_df['x'].iloc[dy_max-1] )
            b = filtered_df['y'].iloc[dy_max-1] - k * filtered_df['x'].iloc[dy_max-1]
            #filtered_df['y_i'] = b + k * filtered_df['x']
            filtered_df['x_i'] = ( filtered_df['y'] - b ) / k
            #filtered_df['y-y_i'] = abs(filtered_df['y_i'] - filtered_df['y'])
            filtered_df['x-x_i'] = abs(filtered_df['x_i'] - filtered_df['x'])
            results = []
            window_start = dy_max
            window_end = dy_max
            window_start_count = 0
            window_end_count = 0
            while window_start >= 0 or window_end < len(filtered_df):
                window_start = dy_max + window_start_count
                window_end = dy_max + window_end_count
                fringe_sum = 0
                if window_start >= 0 and window_end < len(filtered_df) and window_end != window_start:
                    x_total = abs(window_start_count) + abs(window_end_count)
                    x_total = filtered_df['x'].iloc[x_total]
                    t_div1 = filtered_df['x-x_i'].iloc[window_start]
                    phase_1 = filtered_df['y'].iloc[window_start]
                    t_div2 = filtered_df['x-x_i'].iloc[window_end]
                    fringe_sum = t_div1 + t_div2
                    phase_2 = filtered_df['y'].iloc[window_end]
                    t_tan = abs(filtered_df['x_i'].iloc[window_start] - filtered_df['x_i'].iloc[window_end])
                    results.append({
                        'phase': abs(phase_1 - phase_2),
                        'phase_%': 100 * abs(phase_1 - phase_2) / filtered_df['y'].abs().max(),
                        't_total': x_total,
                        't_div1': t_div1,
                        't_div2': t_div2,
                        't_tan': t_tan,
                        't_div/t_tan_%': 100 * fringe_sum / t_tan,
                        't_div/t_total_%': 100 * fringe_sum / x_total
                    })
                window_start_count -= 1
                window_end_count += 1
            results_df = pd.DataFrame(results)
            sheet_id = str(id)
            sheet_ids.append(sheet_id)
            sheet = filtered_df['exp_n'].iloc[0]
            sheets.append(sheet)
            sheet_name = sheet + ' ' + sheet_id
            sheet_names.append(sheet_name)
            ws = wb.create_sheet(title=sheet_name)
            for row in dataframe_to_rows(results_df, index=False, header=True):
                ws.append(row)
            last_col = ws.max_column + 1
            ws.cell(row=1, column=last_col + 1, value='t sweep')  # Header
            ws.cell(row=1, column=last_col + 2, value='t step')  # Header
            ws.cell(row=1, column=last_col + 3, value='t center')  # Header
            ws.cell(row=4, column=last_col + 1, value='t fall')  # Header
            ws.cell(row=4, column=last_col + 2, value='b')        # Header
            ws.cell(row=4, column=last_col + 3, value='k')        # Header
            ws.cell(row=2, column=last_col + 1, value=filtered_df['x'].max())   # Value
            ws.cell(row=2, column=last_col + 2, value=filtered_df['x'].iloc[1])   # Value
            ws.cell(row=2, column=last_col + 3, value=filtered_df['x'].iloc[dy_max])   # Value
            print(sheet_name)
            t_fall = ( results_df['t_tan'][results_df['phase_%'] > 50].reset_index(drop=True).iloc[0] + results_df['t_tan'].iloc[-1] ) / 2
            phase = results_df['phase'][results_df['phase_%'] > 50].reset_index(drop=True).iloc[0]
            t_falls.append(t_fall)
            phases.append(phase)
            ws.cell(row=5, column=last_col + 1, value=t_fall)   # Value
            ws.cell(row=5, column=last_col + 2, value=b)    # Value
            ws.cell(row=5, column=last_col + 3, value=k)    # Value
            ws.cell(row=1, column=last_col + 5, value='Source data')    # Value
            
            last_col = ws.max_column + 1
            new_data_rows = dataframe_to_rows(filtered_df[['x', 'y']], index=False, header=True)
            header_row = next(new_data_rows)
            for col_index, header in enumerate(header_row, start=last_col):
                ws.cell(row=1, column=col_index, value=header)
            for row_index, data_row in enumerate(new_data_rows, start=2):  # Start from the second row
                for col_index, value in enumerate(data_row, start=last_col):
                    ws.cell(row=row_index, column=col_index, value=value)
            
            print('t center:', filtered_df['x'].iloc[dy_max])
            print('b:', b)
            print('k:', k)
            print(results_df.head(10))
        ws = wb.create_sheet(title='descriptor')
        img = Image(r"D:\Gleb\S type plot\bin\phase hydr.jpeg")
        ws.add_image(img, "A1")
        
        
        def create_chart(df, x, y, sheets, cell):
            x_title = str(df.columns[x])
            y_title = str(df.columns[y])
            chart = ScatterChart()
            chart.x_axis.title = x_title
            chart.y_axis.title = y_title
                
            chart.title = y_title + " vs " + x_title
            
            #chart.x_axis.scaling.min = round(filtered_df['x'].min())
            #chart.y_axis.scaling.min = round(-filtered_df['avg_y'].max())
            #chart.x_axis.scaling.max = round(filtered_df['x'].max())
            #chart.y_axis.scaling.max = round(-filtered_df['avg_y'].min())
            
            chart.x_axis.majorGridlines = ChartLines()
            chart.y_axis.majorGridlines = ChartLines()
            chart.x_axis.delete = False
            chart.y_axis.delete = False
            #try:
            #    main_parameters = sorted(main_parameters, key=custom_sort_key)
            #except:
            #    None

            # Loop through each unique main_parameter and add a series to the chart
            for sheet_name in sheet_names:
                x_values = Reference(wb[sheet_name], min_col=x+1, min_row=2, max_row=20)
                y_values = Reference(wb[sheet_name], min_col=y+1, min_row=2, max_row=20)
                series = Series(y_values, x_values, title=sheet_name)
                series.smooth = False
                chart.series.append(series)

            # Place the chart below the data table
            ws.add_chart(chart, cell)
            
        create_chart(results_df, 2, 1, sheets, 'A25')
        create_chart(results_df, 1, 3, sheets, 'J25')
        create_chart(results_df, 1, 4, sheets, 'S25')
        create_chart(results_df, 1, 6, sheets, 'AB25')
        create_chart(results_df, 1, 7, sheets, 'AK25')
        
        ws['Q2'] = 'ID'
        ws['R2'] = 'Experiment'
        ws['S2'] = 'T fall'
        ws['T2'] = 'phase'
        start_row = 3
        for i, (val1, val2, val3, val4) in enumerate(zip(sheet_ids, sheets, t_falls, phases), start=start_row):
            ws.cell(row=i, column=17, value=val1)
            ws.cell(row=i, column=18, value=val2)
            ws.cell(row=i, column=19, value=val3)
            ws.cell(row=i, column=20, value=val4)
        
        
    else:
        unique_params = df['main_parameter'].unique()
        unique_secondarys = df['secondary'].unique()

        df['time_90-10'] = None
        df['phase_90'] = None
        df['phase_max'] = None
        
        for main_parameter in unique_params:
            for secondary in unique_secondarys:
                filtered_df = df[(df['secondary'] == secondary) & (df['main_parameter'] == main_parameter)]

                for id in filtered_df['id'].unique():
                    exp_df = filtered_df[filtered_df['id'] == id].reset_index(drop=True)
                    
                    y_max_idx = exp_df['y'].abs().idxmax()
                    y_max = exp_df['y'].iloc[y_max_idx]
                    
                    y_10 = 0.1 * y_max
                    y_90 = 0.9 * y_max
                        
                    row_10 = exp_df.iloc[(exp_df['y'] - y_10).abs().idxmin()]
                    row_90 = exp_df.iloc[(exp_df['y'] - y_90).abs().idxmin()]
                    
                    x_10 = row_10['x']
                    x_90 = row_90['x']
                    y_10 = row_10['y']
                    y_90 = row_90['y']
                    x_dx = abs(x_90 - x_10)
                    y_dx = y_90
                    # Update df with the R² value
                    df.loc[(df['secondary'] == secondary) & 
                                 (df['id'] == id) & (df['main_parameter'] == main_parameter), 'phase_max'] = y_max
                    df.loc[(df['secondary'] == secondary) & 
                                 (df['id'] == id) & (df['main_parameter'] == main_parameter), 'phase_90'] = y_dx
                    df.loc[(df['secondary'] == secondary) & 
                                 (df['id'] == id) & (df['main_parameter'] == main_parameter), 'time_90-10'] = x_dx
        df = df.drop(columns=['x', 'y']).drop_duplicates().reset_index(drop=True)
        for col in ['phase_max', 'phase_90', 'time_90-10']:
            df[col] = pd.to_numeric(df[col], errors='coerce').round(3)

        df = df.sort_values(by=['main_parameter', 'secondary', 'exp_n', 'id']).reset_index(drop=True)
        
        #param_name = df['param_name'][0].astype(str)
        df = df.drop(columns=['primary', 'param_name']).drop_duplicates().reset_index(drop=True)
        df = df.rename(columns={'secondary': 'time_type'})
        df = df.reindex(columns = ['id', 'exp_n', 'main_parameter', 'time_type', 'phase_max', 'phase_90', 'time_90-10'])
        #print('\nMain parameter: ' + param_name)
        for type in df['time_type'].str[:5].unique():
            sheet_name = f"{type}"
            ws = wb.create_sheet(title=sheet_name)
            filtered_df = df[df['time_type'].str[:5] == type].reset_index(drop=True)
            for row in dataframe_to_rows(filtered_df, index=False, header=True):
                ws.append(row)
            

# Main execution
if __name__ == "__main__":
    # Instructions for creating folder structure and adding test data
    print("""
    How to:
    1. Create a folder to store your data.
    2. Place Excel experiment data in.
    3. Input path to that folder, e.g. 'C:\\folder\\data subfolder'
    4. The program expects filenames in the following example format, where each part is separated by an underscore:
       'JNC Heights 01-07-24_Phase Shifter_Cell Gap_50mkm_15 r_S11_LOGM_0V_2024-07-02_12-47-17'
       This format is interpreted as: name (not used), type (not used), variable parameter name, variable parameter value, 
       experiment number, first fixed parameter, measurable (not used), second fixed parameter, date (not used), time (not used).
       
    """)
    
    try:
        def_state, type, ignore_primary, ignore_secondary, ignore_diff = get_user_setup()
        main_folder_path = summarize_folders()

        raw_df, failed_files = process_files(main_folder_path, def_state)
        if failed_files:
            print("Failed to process the following files:")
            for file, error in failed_files:
                print(f"{file}: {error}")
        
        pre_df, measurable, values = preprocess(raw_df, type, def_state, ignore_primary, ignore_secondary)
        processed_df = process_data(pre_df, def_state, type)
        wb = Workbook()
        for param_name in processed_df['param_name'].unique():
            final_df = processed_df[processed_df['param_name'] == param_name].reset_index(drop=True)
            if def_state == '1':
                    #final_df_0 = calculate_r2(final_df_0, ignore_primary, ignore_secondary, ignore_diff)
                    final_plot(final_df, measurable, values, wb, type)
            else:
                calculate_t(final_df, type)
        # Save the updated Excel file with the chart
        file_name = f"{input(f'Input excel file name\n')}.xlsx"
        wb.save(file_name)
    except Exception as e:
        print(f"Error: {e}\nType: {type(e).__name__}\n")
        traceback.print_exc()
    input("Press Enter to exit\n")
