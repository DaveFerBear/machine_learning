from keras.models import load_model
from keras import optimizers
import pandas as pd
import numpy as np
from helpers import diou, iou, diou_loss, CircleParams
from keras.callbacks import ModelCheckpoint

# Create a ModelCheckpoint callback
checkpoint = ModelCheckpoint(
    'models/circle_cnn_mse1_5_{epoch:02d}.hdf5',  # File path where to save the model
    period=50,                       # Save the model every 50 epochs
    save_weights_only=False          # Save the entire model and not just the weights
)

# Load the previously trained model
model = load_model('models/circle_cnn_mse1_updated5.keras', custom_objects={"diou": diou})

# You can recompile the model with a new optimizer and the reduced learning rate
model.compile(
    loss='MSE',
    optimizer=optimizers.Adam(learning_rate=0.004, beta_1=0.9, beta_2=0.999, epsilon=None, decay=0, amsgrad=False),
    metrics=['accuracy', diou, 'MSE'],  # Update this if you have custom metrics
    run_eagerly=True
)

# Load your training data
x_trainlist = []
y_temp = pd.read_csv("train_set.csv")

for filepath in y_temp['PATH']:
    x_trainlist.append(np.load(filepath))

x_train = np.stack(x_trainlist, axis=0)

y_temp.drop('PATH', axis=1, inplace=True)
y_train = y_temp.to_numpy()

# Continue training the model
model.fit(x=x_train, y=y_train, callbacks=[checkpoint], epochs=1000)  # Adjust the number of epochs as needed

# Save the updated model if needed
model.save('models/circle_cnn_mse1_updated6.keras')

print('Additional Training Completed')
