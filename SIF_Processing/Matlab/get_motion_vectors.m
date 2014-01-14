function vectors = get_motion_vectors(prevImgDir, recentImgDir, vectorOutput)

    % INPUT: previous image parent directory, recent image parent directory
    % FUNCTION: calculates and saves the motion vectors for each photo in a
    % matrix [sensorID prevX prevY newX newY]

    numPrevImgs = 0;
    numRecentImgs = 0;
    prevImgList = dir(fullfile(prevImgDir, '*.jpg'));
    recentImgList = dir(fullfile(recentImgDir, '*.jpg'));


    numPrevImgs = numel(prevImgList);
    numRecentImgs = numel(recentImgList);

    vectors = zeros(numRecentImgs, 5);
    % Loop through each recent image
    for i = 1:numRecentImgs
        recentImg = recentImgList(i).name;
        recentIDIdx = strfind(recentImg, '_');
        recentSensorId = recentImg(recentIDIdx(1)+1: recentIDIdx(2)-1);
        if numPrevImgs == 0
            vectors(i,1) = str2num(recentSensorId);
        end
        % Loop through each previous image
        for j = 1:numPrevImgs

            prevImg = prevImgList(i).name;
            prevIDIdx = strfind(prevImg, '_');
            prevSensorId = prevImg(prevIDIdx(1)+1: prevIDIdx(2)-1);
            % Check if they have the same sensor id
            if(strcmp(recentSensorId, prevSensorId))
                % Calculate the average motion vector between the two
                avgVector = sift_motion(fullfile(prevImgDir, prevImg), fullfile(recentImgDir,recentImg));
                vectorInput = [str2num(recentSensorId) avgVector];
                vectors = [vectors; vectorInput];
                break
            end
        end

    end

    if numPrevImgs > 0
        vectors(1:numRecentImgs,:) = [];
    end
    % Save the vectors as groupID_vectors.ascii
    ttl = sprintf('%s%s_vectors', vectorOutput, recentImg(1:recentIDIdx(1)-1));
    save(ttl, 'vectors', '-ascii');


end
