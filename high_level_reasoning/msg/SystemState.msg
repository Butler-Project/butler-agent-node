builtin_interfaces/Time stamp

# Bitmask indicating which fields are valid in this message
uint8 FIELD_MAP=1
uint8 FIELD_LOCALIZATION=2
uint8 FIELD_LIDAR=4
uint8 FIELD_ODOMETRY=8
uint8 FIELD_LANDMARKS=16
uint8 FIELD_NAV2=32
uint8 FIELD_AMCL=64
uint8 valid_fields

# Map state
uint8 MAP_HAS_MAP=0
uint8 MAP_NOT_AVAILABLE=1
uint8 map_state

# Localization
uint8 LOCALIZATION_OK=0
uint8 LOCALIZATION_NOK=1
uint8 current_location

# Sensors - Lidar
uint8 LIDAR_OK=0
uint8 LIDAR_NOK=1
uint8 lidar_state

# Sensors - Odometry
uint8 ODOMETRY_OK=0
uint8 ODOMETRY_NOK=1
uint8 odometry_state

# Landmarks
uint8 LANDMARKS_OK=0
uint8 LANDMARKS_NOK=1
uint8 landmarks_state
string[] landmark_names

# Nav2
uint8 NAV2_OK=0
uint8 NAV2_NOK=1
uint8 nav2_state

# AMCL Localization
uint8 AMCL_OK=0
uint8 AMCL_NOK=1
uint8 amcl_state
