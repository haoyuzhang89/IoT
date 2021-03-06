import cv2 as cv
import paho.mqtt.client as mqtt

# mqtt parameters
local_mqtt_host = 'broker'
mqtt_port = 1883
mqtt_topic = 'faces'

# global variable indicating disconnect status
dc_flag = False

# create callback functions
def on_connect_local(local_client, userdata, flags, rc):
    """
    This function handles the callback from the broker when it sends acknowledgement of connection status.
    """

    if rc == 0:
        local_client.connected_flag = True
        print("Connected OK returned code = ", rc)
    else:
        print("Bad connection Returned code = ", rc)

def on_disconnect_local(local_client, userdata, rc):
    #global dc_flag
    print("Disconnected due to ", rc)
    #dc_flag = True

# initiate local client instance
local_client = mqtt.Client("detector")

# connection flag indicating connection status
local_client.connected_flag = False

# bind call back functions
local_client.on_connect = on_connect_local
local_client.on_disconnect = on_disconnect_local

# loop start
local_client.loop_start()

# make connection
local_client.connect(local_mqtt_host, mqtt_port, 60)

while not local_client.connected_flag:
    print("Waiting in loop")
    time.sleep(1)

# 1 should correspond to /dev/video1 , your USB camera.
# The 0 is reserved for the NX onboard camera or webcam on laptop
cap = cv.VideoCapture(0)
#cap.set(3, 640)
#cap.set(4, 480)

# alternative approach using background substractor
backSub = cv.createBackgroundSubtractorMOG2()

while True:

    # read frame by frame
    ret, frame = cap.read()

    ## convert frame to gray scale and implement Gaussian blur to remove unnecessary noise
    gray_frame = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
    gray_frame = cv.GaussianBlur(gray_frame, (55, 55), 0)

    # generate foreground mask
    fgmask = backSub.apply(gray_frame)
    fgmask = cv.dilate(fgmask, None, iterations=2)

    # identify contours for moving obejct (foreground mask)
    contours, _ = cv.findContours(fgmask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)

    rectangles = []
    for c in contours:
        try:
            area = cv.contourArea(c)
            rectangles.append((area, cv.boundingRect(c)))
        except:
            pass

        for area, rect in sorted(rectangles, reverse=True):
            if area > 300:
                x, y, w, h = rect
                txt = 'Motion detected'
                txt_2 = 'Sending images to the cloud...'
                cv.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv.putText(frame, txt, (100, 400), cv.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2, cv.LINE_AA)
                cv.putText(frame, txt_2, (100, 430), cv.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 1, cv.LINE_AA)

                # Extract object
                obj_extract = frame[y:y + h, x:x + w]

                # Encode extract to png
                rc, png = cv.imencode('.png', obj_extract)

                # convert png extract to bytes (for messaging)
                msg = png.tobytes()

                #if dc_flag:
                #local_client.connect(local_mqtt_host, mqtt_port, 60)
                local_client.publish(mqtt_topic, msg, qos=1, retain=False)

    cv.imshow('img', frame)
    if cv.waitKey(1) & 0xFF == ord('q'):
        break

# loop end
local_client.disconnect()

cap.release()
cv.destroyAllWindows()
