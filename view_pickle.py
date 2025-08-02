import pickle

with open("docs.pkl", "rb") as f:
    data = pickle.load(f)

# In nội dung để xem
for i, item in enumerate(data[:5]):  # chỉ xem 5 dòng đầu
    print(f"{i}: {item}")
