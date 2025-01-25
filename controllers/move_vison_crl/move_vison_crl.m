% 主控制器函数
function move_vison_crl
    % 初始化 Webots 控制器
    TIME_STEP = 32;
    wb_robot_init();

    % 使用时间戳创建日志文件名
    %timestamp = datestr(now, 'yyyy-mm-dd_HH-MM-SS');
    log_filename =1; %sprintf('log_%s.txt', timestamp);

    % 启动并行池（如果尚未启动）
    if isempty(gcp('nocreate'))
        parpool('local');
    end

    % 启用摄像头并获取摄像头设备
    camera = wb_robot_get_device('CameraTop');
    if camera ~= 0
        wb_camera_enable(camera, TIME_STEP);
        %log_message(log_filename, 'Camera enabled');
        
        % 打印摄像头图像的长和宽
        img_width = wb_camera_get_width(camera);
        img_height = wb_camera_get_height(camera);
        %log_message(log_filename, ...
        %sprintf('Camera image dimensions: Width = %d, Height = %d', img_width, img_height));
    else
        %log_message(log_filename, 'Camera device not found');
    end

    % 启动前进运动的设置
    forwards_motion = wbu_motion_new('../../motions/Forwards.motion');
    wbu_motion_set_loop(forwards_motion, true);

    % 启动并行线程
    % 视觉处理线程
    f1 = parfeval(@vision_task, 0, camera, TIME_STEP, log_filename);

    % 运动控制线程
    f2 = parfeval(@motion_task, 0, forwards_motion, TIME_STEP);

    % 主控制器循环，等待子线程完成
    while wb_robot_step(TIME_STEP) ~= -1
        %if strcmp(f1.State, 'finished') || strcmp(f2.State, 'finished')
            %break;  % 若任何一个线程结束，跳出循环
        %end
        vision_task(camera, TIME_STEP, log_filename)
    end

    % 清理并行任务和 Webots 控制器
    %cancel(f1);
    %cancel(f2);
    wb_robot_cleanup();
end

% 视觉处理任务：执行摄像头图像处理
function vision_task(camera, TIME_STEP, log_filename)
    while true
        % 获取摄像头图像数据
        img_data = wb_camera_get_image(camera);
        
        if ~isempty(img_data)
            % 在图像中替换绿色为红色并计算红色区域几何中心
            [output_image, centroid] = replace_green_with_red(img_data);
            
            % 显示原始图像和处理后的图像
            subplot(1, 2, 1);
            imshow(img_data);
            title('原始图像');
            
            subplot(1, 2, 2);
            imshow(output_image);
            title('绿色区域替换为红色');
            
            % 记录红色区域的几何中心
            if ~isnan(centroid(1))
                %log_message(log_filename, ...
                    %sprintf('Red area centroid: (%.2f, %.2f)', centroid(1), centroid(2)));
            else
                %log_message(log_filename, 'No red area detected.');
            end
            
            % 更新显示
            drawnow;
        else
            %log_message(log_filename, 'Failed to retrieve image data');
        end
        pause(TIME_STEP / 1000);  % 按时间步长暂停
    end
end

% 运动控制任务：控制机器人前进
function motion_task(forwards_motion, TIME_STEP)
    wbu_motion_play(forwards_motion);  % 启动前进动作
    while true
        % 持续执行前进动作
        if ~wbu_motion_is_playing(forwards_motion)
            wbu_motion_play(forwards_motion);  % 若动作结束，重新播放
        end
        pause(TIME_STEP / 1000);  % 按时间步长暂停
    end
end

% 替换绿色区域为红色的函数
function [output_image, centroid] = replace_green_with_red(image)
    % 将图像转换为uint8格式以便后续处理
    image = uint8(image);  
    output_image = image;  % 创建输出图像
    
    % 定义绿色的RGB范围
    green_low = [0, 200, 0];       % 绿色下限（RGB）
    green_high = [120, 255, 120];   % 绿色上限（RGB）
    
    % 初始化红色区域的坐标列表
    red_pixels = [];
    
    % 遍历图像的每一个像素
    [rows, cols, ~] = size(image);
    for i = 1:rows
        for j = 1:cols
            % 获取当前像素的 RGB 值
            R = image(i, j, 1);
            G = image(i, j, 2);
            B = image(i, j, 3);
            
            % 判断当前像素是否在绿色范围内
            if R >= green_low(1) && R <= green_high(1) && ...
               G >= green_low(2) && G <= green_high(2) && ...
               B >= green_low(3) && B <= green_high(3)
                % 将绿色像素替换为红色
                output_image(i, j, :) = [255, 0, 0];
                % 将红色像素的坐标添加到列表
                red_pixels = [red_pixels; i, j];
            end
        end
    end
    
    % 计算红色区域的几何中心
    if ~isempty(red_pixels)
        centroid = mean(red_pixels, 1);  % 计算几何中心
    else
        centroid = [NaN, NaN];  % 如果没有红色像素，返回NaN
    end
end

% 记录日志的辅助函数
%function log_message(log_filename, message)
%    fid = fopen(log_filename, 'a');  % 以追加模式打开日志文件
%    if fid ~= -1
%        fprintf(fid, '%s: %s\n', datestr(now, 'yyyy-mm-dd HH:MM:SS'), message);
%        fclose(fid);
%    else
%        disp('Failed to open log file');
%    end
%end
