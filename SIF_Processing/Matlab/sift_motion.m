function [avgVector] = sift_motion(prevImg,recentImg)
% SIFT_motion Demonstrates matching two images using SIFT and RANSAC

im1 = imread(prevImg);
im2 = imread(recentImg);

% make single
im1 = im2single(im1) ;
im2 = im2single(im2) ; 

% make grayscale
if size(im1,3) > 1, im1g = rgb2gray(im1) ; else im1g = im1 ; end
if size(im2,3) > 1, im2g = rgb2gray(im2) ; else im2g = im2 ; end


% --------------------------------------------------------------------
%                                                         SIFT matches
% --------------------------------------------------------------------

[f1,d1] = vl_sift(im1g) ;
[f2,d2] = vl_sift(im2g) ;

[matches, scores] = vl_ubcmatch(d1,d2) ;

numMatches = size(matches,2) ;

X1 = f1(1:2,matches(1,:)) ; X1(3,:) = 1 ;
X2 = f2(1:2,matches(2,:)) ; X2(3,:) = 1 ;

% --------------------------------------------------------------------
%                                         RANSAC with homography model
% --------------------------------------------------------------------

clear H score ok ;
for t = 1:100
  % estimate homograpyh
  subset = vl_colsubset(1:numMatches, 4) ;
  A = [] ;
  for i = subset
    A = cat(1, A, kron(X1(:,i)', vl_hat(X2(:,i)))) ;
  end
  [U,S,V] = svd(A) ;
  H{t} = reshape(V(:,9),3,3) ;

  % score homography
  X2_ = H{t} * X1 ;
  du = X2_(1,:)./X2_(3,:) - X2(1,:)./X2(3,:) ;
  dv = X2_(2,:)./X2_(3,:) - X2(2,:)./X2(3,:) ;
  ok{t} = (du.*du + dv.*dv) < 6*6;
  score(t) = sum(ok{t}) ;
end

[score, best] = max(score) ;
H = H{best} ;
ok = ok{best} ;


% --------------------------------------------------------------------
%                                                         Show matches
% --------------------------------------------------------------------

% dh1 = max(size(im2,1)-size(im1,1),0) ;
% dh2 = max(size(im1,1)-size(im2,1),0) ;

% figure(1) ; clf ;
% 
% imagesc([padarray(im1,dh1,'post') padarray(im2,dh2,'post')]) ;
% o = size(im1,2) ;
% truesize;

f1xm = f1(1,matches(1,ok));
f1ym = f1(2,matches(1,ok));

f2xm = f2(1,matches(2,ok));
f2ym = f2(2,matches(2,ok));

vectors = [f1xm' f1ym' f2xm' f2ym'];

avgVector = mean(vectors,1);

% arrow([avgVector(1); avgVector(2)],[avgVector(3);avgVector(4)]);
% arrow([vectors(:,1)';vectors(:,2)'],[vectors(:,3)';vectors(:,4)']);
% 
% arrow([f1xm+o;f1ym], ...
%      [f2xm+o;f2ym]) ;
% 
% title(sprintf('%d (%.2f%%) inliner matches out of %d', ...
%               sum(ok), ...
%               100*sum(ok)/numMatches, ...
%               numMatches)) ;
% axis image off ;
% 
% drawnow ;

% Set motion (an image type) to the figure(1) 
% f = getframe;
% [im,map] = frame2im(f);    %Return associated image data
% if isempty(map)            %Truecolor system
%   motion = im;
% else                       %Indexed system
%   motion = ind2rgb(im,map);   %Convert image data
% end
    




end

% 
% ima = imread('/Users/cole_d/MATLAB/Capstone/SIFT/test/test1.jpg');
% imb = imread('/Users/cole_d/MATLAB/Capstone/SIFT/test/test2.jpg');
% 
% sift_motion(im1,im2,1);

