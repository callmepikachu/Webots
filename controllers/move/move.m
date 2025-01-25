% Description: MATLAB controller for NAO robot to move forward
function move

% Control step
TIME_STEP = 40;

% Get and enable the foot sensors
fsr(1) = wb_robot_get_device('LFsr');  % Left foot sensor
fsr(2) = wb_robot_get_device('RFsr');  % Right foot sensor
wb_touch_sensor_enable(fsr(1), TIME_STEP);
wb_touch_sensor_enable(fsr(2), TIME_STEP);

% Initialize the robot motion
forwards_motion = wbu_motion_new('../../motions/Forwards.motion');
wbu_motion_set_loop(forwards_motion, true);
wbu_motion_play(forwards_motion);

% Count the steps
steps = 0;

while wb_robot_step(TIME_STEP) ~= -1
    steps = steps + 1;

    % Get foot sensor values
    fsv(1,:) = wb_touch_sensor_get_values(fsr(1));
    fsv(2,:) = wb_touch_sensor_get_values(fsr(2));

    % Calculate left and right foot pressures (optional, can be removed)
    l(1) = fsv(1,3)/3.4 + 1.5*fsv(1,1) + 1.15*fsv(1,2); % Left Foot Front Left
    l(2) = fsv(1,3)/3.4 + 1.5*fsv(1,1) - 1.15*fsv(1,2); % Left Foot Front Right
    l(3) = fsv(1,3)/3.4 - 1.5*fsv(1,1) - 1.15*fsv(1,2); % Left Foot Rear Right
    l(4) = fsv(1,3)/3.4 - 1.5*fsv(1,1) + 1.15*fsv(1,2); % Left Foot Rear Left

    r(1) = fsv(2,3)/3.4 + 1.5*fsv(2,1) + 1.15*fsv(2,2); % Right Foot Front Left
    r(2) = fsv(2,3)/3.4 + 1.5*fsv(2,1) - 1.15*fsv(2,2); % Right Foot Front Right
    r(3) = fsv(2,3)/3.4 - 1.5*fsv(2,1) - 1.15*fsv(2,2); % Right Foot Rear Right
    r(4) = fsv(2,3)/3.4 - 1.5*fsv(2,1) + 1.15*fsv(2,2); % Right Foot Rear Left

    % Optional: Display foot pressure (could be removed if not needed)
    left_pressure = sum(l);
    right_pressure = sum(r);
    disp(['Left Foot Pressure: ', num2str(left_pressure), ' N']);
    disp(['Right Foot Pressure: ', num2str(right_pressure), ' N']);
end

% Cleanup code
wb_robot_cleanup();
