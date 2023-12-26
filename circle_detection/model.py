from keras.models import Sequential
from keras.layers import Conv2D, MaxPooling2D, BatchNormalization
from keras.layers import Activation, Dropout, Flatten, Dense
from keras import optimizers
from keras.metrics import Accuracy
from keras.callbacks import ModelCheckpoint

from keras import backend as K

# from helpers import iou, loss_iou, CircleParams
from helpers import diou, iou, diou_loss, CircleParams

import pandas as pd
import numpy as np
import tensorflow as tf
# import tensorflow_addons as tfa
# from tensorflow_addons.losses.giou_loss import giou_loss

# Create a ModelCheckpoint callback
checkpoint = ModelCheckpoint(
    'model_epoch_{epoch:02d}.hdf5',  # File path where to save the model
    period=50,                       # Save the model every 50 epochs
    save_weights_only=False          # Save the entire model and not just the weights
)

train_results_path = "datasets/trainset/"

model = Sequential()

# model.add(Conv2D(filters = 32, kernel_size = 5, data_format = 'channels_first', input_shape=(1, 1, 200, 200), output_shape=(32, 32, 98, 98)))
model.add(Conv2D(32, (3, 3), input_shape=(200, 200, 1)))
model.add(BatchNormalization())
model.add(Activation('relu'))
model.add(MaxPooling2D(pool_size=(2, 2)))

# model.add(Conv2D(filters = 64, kernel_size = 3, data_format = 'channels_first', input_shape=(32, 32, 98, 98), output_shape=(64, 64, 48, 48)))
model.add(Conv2D(64, (5, 5)))
model.add(BatchNormalization())
model.add(Activation('relu'))
model.add(MaxPooling2D(pool_size=(2, 2)))

# model.add(Conv2D(filters = 128, kernel_size = 3, data_format = 'channels_first', input_shape=(64, 64, 48, 48), output_shape=(128, 128, 23, 23)))
model.add(Conv2D(128, (3, 3)))
model.add(BatchNormalization())
model.add(Activation('relu'))
model.add(MaxPooling2D(pool_size=(2, 2)))

# model.add(Conv2D(filters = 4, kernel_size = 1, data_format = 'channels_first', input_shape=(128, 128, 23, 23), output_shape=(128, 4, 21, 21)))
model.add(Conv2D(4, (1, 1)))
model.add(BatchNormalization())
model.add(Activation('relu'))

# Fully Connected Layers
model.add(Flatten())
model.add(Dense(256, input_shape=(4*21*21,)))
model.add(Activation('relu'))
model.add(Dropout(0.5))
model.add(Dense(16, input_shape=(256,)))
model.add(Activation('relu'))
model.add(Dense(3, input_shape=(16,)))

# model.add(Dense(128, input_shape=(256,)))
# model.add(Dropout(0.5))
# model.add(Activation('relu'))
# model.add(Dense(16, input_shape=(128,)))
# model.add(Dropout(0.5))
# model.add(Activation('relu'))
# model.add(Dense(3, input_shape=(16,)))



# Optimizers + Compile
adam_opt = optimizers.Adam(learning_rate=0.008, beta_1=0.9, beta_2=0.999, epsilon=None, decay=0.005, amsgrad=False)
model.compile(loss='MSE',
              #optimizer=adam_opt,
              optimizer=optimizers.RMSprop(lr=.02),
              metrics=[diou],
              run_eagerly=True)

x_trainlist = []
y_temp = pd.read_csv("train_set.csv")

for filepath in y_temp['PATH']:
    x_trainlist.append(np.load(filepath))

# y_params = [CircleParams(y_temp['ROW'][i], y_temp['COL'][i], y_temp['RAD'][i]) for i in range(len(y_temp['PATH']))]

x_train = np.stack(x_trainlist, axis=0)
# print(type(x_train))

y_temp.drop('PATH', axis=1, inplace=True)
y_train = y_temp.to_numpy()
# y_train2 = np.stack(y_params, axis=0)


# Continue training the model
model.fit(
    x=x_train, 
    y=y_train, 
    epochs=250, 
    callbacks=[checkpoint]  # Add the checkpoint callback here
)

print('Finished Training')

model.save('circle_cnn_net_variant_2.keras')