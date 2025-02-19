import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression

# Define 9 sample points
X_data = np.array([
    [0, 0], [0, 1], [0, 2],
    [1, 0], [1, 1], [1, 2],
    [2, 0], [2, 1], [2, 2]
])  # Independent variables (x, y)

y1 = [49.7, 50.6, 44.3, 63, 52.7, 45.8, 60.5, 56.5, 49.5]
y2 = [61.5, 50.8, 48.5, 53.7, 55.5, 52.5, 55.5, 52.9, 54.5]
y3 = [52.7, 50.8, 47, 50.7, 47.8, 48.3, 61, 60.5, 53.6]
y4 = [54.6, 50.7, 46.6, 55.8, 52.0, 48.9, 59.0, 56.6, 52.5]

ys = [y1, y2, y3, y4]
for y in ys:
    
    Z_data = np.array(y)  # Dependent variable (z)

    # Polynomial feature transformation (quadratic)
    poly = PolynomialFeatures(degree=3)
    X_poly = poly.fit_transform(X_data)

    # Fit a regression model
    model = LinearRegression()
    model.fit(X_poly, Z_data)

    # Create a meshgrid for surface plotting
    x_range = np.linspace(0, 2, 50)
    y_range = np.linspace(0, 2, 50)
    X_mesh, Y_mesh = np.meshgrid(x_range, y_range)
    X_mesh_flat = np.c_[X_mesh.ravel(), Y_mesh.ravel()]
    X_mesh_poly = poly.transform(X_mesh_flat)

    # Predict Z values
    Z_pred = model.predict(X_mesh_poly).reshape(X_mesh.shape)

    # Plot the response surface
    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(111, projection='3d')
    ax.plot_surface(X_mesh, Y_mesh, Z_pred, cmap='viridis', alpha=0.7)
    ax.scatter(X_data[:, 0], X_data[:, 1], Z_data, color='red', label='Data Points')
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    plt.show()
