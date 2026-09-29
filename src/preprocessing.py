import cv2


def preprocess_image(image_path):

    image = cv2.imread(image_path)

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    gaussian = cv2.GaussianBlur(gray, (5, 5), 0)

    threshold_value = 127

    binary = cv2.threshold(
        gaussian,
        threshold_value,
        255,
        cv2.THRESH_BINARY
    )

    return binary[1]