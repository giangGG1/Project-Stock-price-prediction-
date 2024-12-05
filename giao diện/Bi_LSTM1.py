import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error, mean_absolute_percentage_error
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, LSTM, Bidirectional
from sklearn.metrics import mean_squared_error

# path = "C:/Users/admin/OneDrive/maytinh/Downloads/New folder/META_stock_data.csv"
path =" "
# Load the data
data = data = pd.read_csv(path) 

def calculate_RSI(data, window=21):
    delta = data['Close'].diff(1)
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    RS = gain / loss
    RSI = 100 - (100 / (1 + RS))
    return RSI

data['RSI'] = calculate_RSI(data)

# Bước 3: Tính MA
def calculate_MA(data, window=21):
    return data['Close'].rolling(window=window).mean()

data['MA'] = calculate_MA(data)
data = data.dropna()  # Loại bỏ các hàng chứa giá trị NaN do tính RSI và MA


# Tính toán số lượng dòng cho từng phần
total_rows = len(data)
train_size = int(0.8 * total_rows)
val_size = int(0.1 * total_rows)
test_size = total_rows - train_size - val_size  # Đảm bảo rằng tổng số dòng vẫn bằng total_rows

# Xử lý các giá trị vô hạn hoặc quá lớn
data.replace([np.inf, -np.inf], np.nan, inplace=True)
data.dropna(how='any', axis=0, inplace=True)

# Chia DataFrame thành các tập huấn luyện, kiểm tra và kiểm định
data_train = data.iloc[:train_size]
data_val = data.iloc[train_size:train_size + val_size]
data_test = data.iloc[train_size + val_size:]


# Chuẩn hóa các cột giá dựa trên tập huấn luyện và áp dụng cho tập kiểm tra và kiểm định
scaler_price = MinMaxScaler(feature_range=(-1, 1))
price_columns = ['Close', 'Open', 'RSI', 'MA','High','Low']
data_train[price_columns] = scaler_price.fit_transform(data_train[price_columns])
data_val[price_columns] = scaler_price.transform(data_val[price_columns])
data_test_copy=data_test[price_columns]
data_test[price_columns] = scaler_price.transform(data_test[price_columns])

# Chuyển đổi các cột pandas thành mảng NumPy
train_data = data_train[price_columns].values
val_data = data_val[price_columns].values
test_data = data_test[price_columns].values

# Training data
seq_len = 21
X_train, y_train = [], []
for i in range(seq_len, len(train_data)):
  X_train.append(train_data[i-seq_len:i]) # Chunks of training data with a length of 128 df-rows
  y_train.append(train_data[:, 0][i]) #Value of 4th column (Close Price) of df-row 128+1
X_train, y_train = np.array(X_train), np.array(y_train)



# Validation data
X_val, y_val = [], []
for i in range(seq_len, len(val_data)):
    X_val.append(val_data[i-seq_len:i])
    y_val.append(val_data[:, 0][i])
X_val, y_val = np.array(X_val), np.array(y_val)


# Test data
X_test, y_test = [], []
for i in range(seq_len, len(test_data)):
    X_test.append(test_data[i-seq_len:i])
    y_test.append(test_data[:, 0][i])    
X_test, y_test = np.array(X_test), np.array(y_test)


model = Sequential()
model.add(Bidirectional(LSTM(50, activation='relu'), input_shape=(21, 6)))
model.add(Dense(1))
model.compile(optimizer='adam', loss='mean_squared_error')

# Train the model
model.fit(X_train, y_train, epochs=100, batch_size=32, validation_data=(X_val, y_val), verbose=1)

# Predicting and reversing normalization
predicted_stock_price = model.predict(X_test)
predicted_stock_price = scaler_price.inverse_transform(np.concatenate((predicted_stock_price, np.zeros((len(predicted_stock_price), 5))), axis=1))[:,0]


# Get actual prices from the last part of the test set
actual_prices = data_test_copy['Close'].values[seq_len:]


# print('Gía trị dự đoán',predicted_stock_price)

# Predicting next 7 days
def predict_next_days(model, last_sequence, num_days=7):
    predictions = []
    current_sequence = last_sequence

    for _ in range(num_days):
        next_pred = model.predict(current_sequence[np.newaxis, :, :])[0, 0]
        predictions.append(next_pred)

        next_pred_scaled = scaler_price.transform(np.array([[next_pred, 0, 0, 0, 0, 0]]))[0, 0]

        current_sequence = np.append(current_sequence[1:], [[next_pred_scaled, 0, 0, 0, 0, 0]], axis=0)

    return predictions

last_sequence = test_data[-seq_len:]
next_7_days_predictions = predict_next_days(model, last_sequence)
next_7_days_predictions = scaler_price.inverse_transform(np.concatenate((np.array(next_7_days_predictions).reshape(-1, 1), np.zeros((7, 5))), axis=1))[:, 0]

print('Next 7 days predictions:', next_7_days_predictions)