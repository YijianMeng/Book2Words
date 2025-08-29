import cv2

# 0 = default camera (MacBook webcam, or iPhone if Continuity Camera is active)
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: Could not open camera")
    exit()

# Capture a single frame
ret, frame = cap.read()
if ret:
    cv2.imwrite("captured_image.jpg", frame)
    print("Image saved as captured_image.jpg")
else:
    print("Error: Could not read frame")

cap.release()
cv2.destroyAllWindows()
