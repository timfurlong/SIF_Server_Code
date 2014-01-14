function set_forecasts(inputImgDir, forecastDir, lightIntensity)
    % INPUT: parent input image directory, parent forecast directory to
    % output to, light intensity
    % FUNCTION: loops through each image in inputImgDir and creates the
    % forecast image and saves in forecastDir as the input file name appended with 'forecast.jpg'
    % according to the given light intensity

    inputImgList = dir(fullfile(inputImgDir, '*.jpg'));
    
    numInputImgs = numel(inputImgList);
    % Loop through each input image
    for i = 1: numInputImgs
        inputImg = fullfile(inputImgDir, inputImgList(i).name);
        filename = inputImgList(i).name;
        filename = filename(1:length(filename)-4);
        % append 'forecast.jpg' onto the filename
        ttl = sprintf('%s_forecast.jpg', filename);
        ttl = strcat(forecastDir,ttl);
        % Create and save forecast map
        forecastor(inputImg, ttl, lightIntensity);
        
    end

end