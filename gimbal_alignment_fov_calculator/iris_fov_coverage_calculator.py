# parameters

import math
from turtle import left


# key input parameters
IPD=63
eyeball_radius=12
eye_to_camera_distance=350
eye_center_to_camera_center_offset=0
left_camera_to_right_camera_distance=42
camera_h_fov=5.6
gimbal_angle=4   # 2x actuator range due to prism reflection, one side angle 

# calculations
left_camera_x=-left_camera_to_right_camera_distance/2
left_camera_y=0
right_camera_x=left_camera_to_right_camera_distance/2
right_camera_y=0


left_eye_x1=-eyeball_radius-IPD/2+eye_center_to_camera_center_offset
left_eye_y1=eye_to_camera_distance

left_eye_x2=eyeball_radius-IPD/2+eye_center_to_camera_center_offset
left_eye_y2=eye_to_camera_distance

right_eye_x1=-eyeball_radius+IPD/2+eye_center_to_camera_center_offset
right_eye_y1=eye_to_camera_distance

right_eye_x2=eyeball_radius+IPD/2+eye_center_to_camera_center_offset
right_eye_y2=eye_to_camera_distance



#calcuate the angles between the left eye to left camera and right eye to right camera
# left eye point 1 to camera
left_eye_to_left_camera_angle1=math.atan2(left_eye_y1-left_camera_y,left_eye_x1-left_camera_x)
# left eye point 2 to camera
left_eye_to_left_camera_angle2=math.atan2(left_eye_y2-left_camera_y,left_eye_x2-left_camera_x)

left_eye_coverage=-math.degrees(left_eye_to_left_camera_angle2-left_eye_to_left_camera_angle1)
left_eye_fov_margin=camera_h_fov-left_eye_coverage
left_eye_fov_margin_with_gimbal_angle=left_eye_fov_margin+gimbal_angle

# right eye point 1 to camera
right_eye_to_right_camera_angle1=math.atan2(right_eye_y1-right_camera_y,right_eye_x1-right_camera_x)
# right eye point 2 to camera
right_eye_to_right_camera_angle2=math.atan2(right_eye_y2-right_camera_y,right_eye_x2-right_camera_x)

right_eye_coverage=-math.degrees(right_eye_to_right_camera_angle2-right_eye_to_right_camera_angle1)
right_eye_fov_margin=camera_h_fov-right_eye_coverage
right_eye_fov_margin_with_gimbal_angle=right_eye_fov_margin+gimbal_angle    



# key outputs
print("Left eye coverage: ", left_eye_coverage)
print("Left eye FOV margin: ", left_eye_fov_margin)
print("Left eye FOV margin with gimbal angle: ", left_eye_fov_margin_with_gimbal_angle)


print("Right eye coverage: ", right_eye_coverage)
print("Right eye FOV margin: ", right_eye_fov_margin)
print("Right eye FOV margin with gimbal angle: ", right_eye_fov_margin_with_gimbal_angle)