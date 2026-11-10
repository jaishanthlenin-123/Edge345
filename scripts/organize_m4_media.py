import os
import shutil
import cv2
import numpy as np

src_dir = "photos and videos"
base_m4 = "evidence/M4"

# Mappings: (source_filename, dest_subfolder, dest_filename, description)
# We will copy photos and videos into evidence/M4/
media_mapping = [
    # Category 01: Sensor Data
    {
        "src": "me_working_photo.jpeg",
        "dest_dir": os.path.join(base_m4, "01_sensor_data", "screenshots"),
        "dest_name": "me_working_photo.jpeg",
        "category": "01_sensor_data",
        "type": "image",
        "desc": "Developer working at the hardware workbench calibrating Arduino Uno and sensors."
    },
    {
        "src": "me_working_photo2.jpeg",
        "dest_dir": os.path.join(base_m4, "01_sensor_data", "screenshots"),
        "dest_name": "me_working_photo2.jpeg",
        "category": "01_sensor_data",
        "type": "image",
        "desc": "Developer reviewing live telemetry stream and sensor connections on workbench."
    },
    {
        "src": "sensor_values shown in terminal.jpeg",
        "dest_dir": os.path.join(base_m4, "01_sensor_data", "screenshots"),
        "dest_name": "sensor_values_shown_in_terminal.jpeg",
        "category": "01_sensor_data",
        "type": "image",
        "desc": "Terminal console displaying live 10-field CSV telemetry rows received from Arduino."
    },
    {
        "src": "sensor_values shown in terminall.jpeg",
        "dest_dir": os.path.join(base_m4, "01_sensor_data", "screenshots"),
        "dest_name": "sensor_values_shown_in_terminall.jpeg",
        "category": "01_sensor_data",
        "type": "image",
        "desc": "Secondary terminal console capture confirming continuous stable telemetry parsing."
    },
    {
        "src": "Dashboard.jpeg",
        "dest_dir": os.path.join(base_m4, "01_sensor_data", "screenshots"),
        "dest_name": "dashboard_live_telemetry.jpeg",
        "category": "01_sensor_data",
        "type": "image",
        "desc": "Web monitoring dashboard displaying real-time sensor gauges (Angle, Voltage, Current, Vibration, Acoustic)."
    },
    {
        "src": "Initial_configuration.mp4",
        "dest_dir": os.path.join(base_m4, "01_sensor_data", "videos"),
        "dest_name": "initial_hardware_configuration.mp4",
        "category": "01_sensor_data",
        "type": "video",
        "frame_name": "initial_hardware_configuration_frame.png",
        "desc": "Workbench video showing complete edge acquisition hardware, breadboard wiring, Arduino, and sensors."
    },
    {
        "src": "intial_configuration of servo motor.mp4",
        "dest_dir": os.path.join(base_m4, "01_sensor_data", "videos"),
        "dest_name": "initial_configuration_servo_motor.mp4",
        "category": "01_sensor_data",
        "type": "video",
        "frame_name": "servo_motor_mounting_and_wiring_frame.png",
        "desc": "Video showing SG90 servo motor mounting, PWM signal line, and 5V supply connection."
    },
    {
        "src": "sensor_values_showing in serial moniter.mp4",
        "dest_dir": os.path.join(base_m4, "01_sensor_data", "videos"),
        "dest_name": "sensor_values_showing_in_serial_monitor.mp4",
        "category": "01_sensor_data",
        "type": "video",
        "frame_name": "serial_monitor_streaming_frame.png",
        "desc": "Video capturing Arduino Serial Monitor streaming real-time CSV sensor data at 115200 baud."
    },
    {
        "src": "serial moniter showing the values of the sensors from the servomotor.mp4",
        "dest_dir": os.path.join(base_m4, "01_sensor_data", "videos"),
        "dest_name": "serial_monitor_servo_sensor_stream.mp4",
        "category": "01_sensor_data",
        "type": "video",
        "frame_name": "serial_monitor_servo_sensor_stream_frame.png",
        "desc": "High-resolution desktop video demonstrating synchronized multi-sensor telemetry during servo motion cycles."
    },
    {
        "src": "values_showing.mp4",
        "dest_dir": os.path.join(base_m4, "01_sensor_data", "videos"),
        "dest_name": "values_showing.mp4",
        "category": "01_sensor_data",
        "type": "video",
        "frame_name": "telemetry_values_live_stream_frame.png",
        "desc": "Video showing real-time numeric value updates from ACS712, Voltage divider, and MPU6050."
    },
    {
        "src": "video_showing_sensorvalues_stepper_motor.mp4",
        "dest_dir": os.path.join(base_m4, "01_sensor_data", "videos"),
        "dest_name": "servo_motion_and_sensorvalues_demonstration.mp4",
        "category": "01_sensor_data",
        "type": "video",
        "frame_name": "servo_motion_and_sensorvalues_frame.png",
        "desc": "Demonstration video showing SG90 servo motor angular movement and synchronized sensor logging (corrected: SG90 servo motor, despite legacy 'stepper_motor' video filename)."
    },
    # Category 02: Anomaly Model & Category 03: False Alarms
    {
        "src": "Video showing anamaly.mp4",
        "dest_dir": os.path.join(base_m4, "02_anomaly_model", "videos"),
        "dest_name": "video_showing_anomaly.mp4",
        "category": "02_anomaly_model",
        "type": "video",
        "frame_name": "anomaly_detection_event_frame.png",
        "desc": "Demonstration video showing mechanical anomaly injection on the SG90 servo and real-time anomaly alarm trigger."
    }
]

def extract_best_frame(video_path, output_path):
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    best_frame = None
    best_var = -1
    
    # Sample 10 evenly spaced frames between 15% and 85%
    sample_indices = np.linspace(int(total_frames * 0.15), int(total_frames * 0.85), 10, dtype=int)
    for idx in sample_indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = cap.read()
        if ret:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            var = cv2.Laplacian(gray, cv2.CV_64F).var()
            if var > best_var:
                best_var = var
                best_frame = frame
                
    cap.release()
    if best_frame is not None:
        cv2.imwrite(output_path, best_frame)
        print(f"Extracted frame: {output_path} (sharpness: {best_var:.1f})")
        return True
    return False

def main():
    print("Beginning media file organization and verification...")
    
    # Also copy Dashboard to Category 02 screenshots because it illustrates anomaly detection status
    dashboard_src = os.path.join(src_dir, "Dashboard.jpeg")
    cat2_dashboard = os.path.join(base_m4, "02_anomaly_model", "screenshots", "dashboard_anomaly_detected.jpeg")
    shutil.copy2(dashboard_src, cat2_dashboard)
    print(f"Copied dashboard to Category 02: {cat2_dashboard}")

    for item in media_mapping:
        src_path = os.path.join(src_dir, item["src"])
        dest_path = os.path.join(item["dest_dir"], item["dest_name"])
        
        if not os.path.exists(src_path):
            raise FileNotFoundError(f"Missing source file: {src_path}")
            
        os.makedirs(item["dest_dir"], exist_ok=True)
        shutil.copy2(src_path, dest_path)
        size_mb = os.path.getsize(dest_path) / (1024 * 1024)
        print(f"Copied: {item['src']} -> {dest_path} ({size_mb:.2f} MB)")
        
        # If video, extract a high quality frame to screenshots folder of that category
        if item["type"] == "video" and "frame_name" in item:
            screens_dir = os.path.join(base_m4, item["category"], "screenshots")
            os.makedirs(screens_dir, exist_ok=True)
            frame_path = os.path.join(screens_dir, item["frame_name"])
            extract_best_frame(src_path, frame_path)
            
    # Clean up temporary extracted frames in photos and videos if any
    temp_frames = os.path.join(src_dir, "extracted_frames")
    if os.path.exists(temp_frames):
        shutil.rmtree(temp_frames)
        print(f"Removed temporary directory: {temp_frames}")

    print("\nAll 12 media files successfully mapped and processed!")

if __name__ == "__main__":
    main()
