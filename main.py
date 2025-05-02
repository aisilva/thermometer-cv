import numpy as np
import cv2 as cv
import math


cap = cv.VideoCapture(0)
if not cap.isOpened():
    print("Cannot open camera")
    exit()

while True:
    # Capture frame-by-frame
    ret, frame = cap.read()
    
    # if frame is read correctly ret is True
    if not ret:
        print("Can't receive frame (stream end?). Exiting ...")
        break
    # Our operations on the frame come here


    def fahrenheit(angle):
        #hard-coding the particular thermometer I am using
        return -78 + (58* angle)/90

    def celsius(angle):
        return 5* (fahrenheit(angle) - 32) /9
    
    
    def contour_finder(image):
        #grayscale
        gray = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
        #threshold
        th, im_th = cv.threshold(gray, 0, 255, cv.THRESH_BINARY_INV+cv.THRESH_OTSU)
        #im_th = cv.bitwise_not(im_th)
        #th, im_th = cv.threshold(gray, 128, 255, cv.THRESH_BINARY)
    
        edges = cv.Canny(im_th, 100, 200)
    
        contours, hierarchy = cv.findContours(edges, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
        cnt = contours
        big_contour_temp = -1
        
        maxm = 0
        for i in cnt:
            area = cv.contourArea(i) #find the contour having largest area
            
            if area>maxm:
                maxm = area
                big_contour_temp = i
                
            
        return [big_contour_temp, maxm]


    lst = contour_finder(frame)
    big_contour = lst[0]
    maxm = lst[1]
    final = cv.drawContours(frame, big_contour, -1, (0, 255, 0), 3)

    
    #assume biggest contour is thermometer ellipse
    ellipse = cv.fitEllipse(big_contour)
    ellipse_center = ellipse[0]
    ellipse_axes = ellipse[1]
    ellipse_angle = ellipse[2]
    #output is ((x,y), (majorAxis, minorAxis), angle)
    #center, lengths of axes, rotation angle
    
    cv.ellipse(final, ellipse, (255,255,0), 2)

    mask = np.zeros_like(final)
    rows, cols, _ = mask.shape
    mask = cv.ellipse(mask, ellipse, color=(255,255,255), thickness=-1)

    result = np.bitwise_and(final, mask)
    final = result

   
    #perspective transform

    #get bounding box on ellipse
    x,y,w,h = cv.boundingRect(big_contour)

    cv.rectangle(final, (x,y), (x+w, y+h), (36, 255, 12), 2)

    #final = cv.circle(final, (int(ellipse_center[0]), int(ellipse_center[1])), 10, (0,0,255), thickness=-1)

    x0 = ellipse_center[0]
    y0 = ellipse_center[1]

    x1 = x0 + int(0.5*ellipse_axes[0]*math.cos(0))
    y1 = y0 + int(0.5*ellipse_axes[1]*math.sin(0))

    x2 = x0 + int(0.5*ellipse_axes[0]*math.cos(math.pi*1/2))
    y2 = y0 + int(0.5*ellipse_axes[1]*math.sin(math.pi*1/2))

    x3 = x0 + int(0.5*ellipse_axes[0]*math.cos(math.pi*1))
    y3 = y0 + int(0.5*ellipse_axes[1]*math.sin(math.pi*1))

    x4 = x0 + int(0.5*ellipse_axes[0]* math.cos(math.pi*3/2))
    y4 = y0 + int(0.5*ellipse_axes[1]*math.sin(math.pi*3/2))

    
    #final = cv.circle(final, (int(x0),int(y0)), 10, (0,0,255), thickness=-1)
    #frame = cv.circle(frame, (int(x1),int(y1)), 10, (0,0,255), thickness=-1)
    #frame = cv.circle(frame, (int(x2),int(y2)), 10, (0,0,255), thickness=-1)
    #frame = cv.circle(frame, (int(x3),int(y3)), 10, (0,0,255), thickness=-1)
    #frame = cv.circle(frame, (int(x4),int(y4)), 10, (0,0,255), thickness=-1)

    x_max = max(x1,x2,x3,x4)
    y_max = max(y1,y2,y3,y4)
    x_min = min(x1,x2,x3,x4)
    y_min = min(y1,y2,y3,y4)


    #this bit still needs work
    #center = ellipse_center
    #rotate_matrix = cv.getRotationMatrix2D(center=center, angle=ellipse_angle, scale=1)
    #print(ellipse_angle)
    #rotated_image=cv.warpAffine(src=final, M=rotate_matrix, dsize=(w,h))
    #final=rotated_image

    
    #bounding box should be square, transform it if not
    #this does turn the box into a square, but the ellipse is still skewed
    if w != h:

        box_size = 600
        offset =0

        src_pts = np.array([[x_min, y_min], [x_max, y_min], [x_max,y_max],[x_min, y_max]], dtype=np.float32)
        #src_pts = np.array([[x4-offset, y1+offset], [x2+offset, y1+offset], [x2+offset, y3-offset], [x4-offset, y3-offset]], dtype=np.float32)
        dst_pts = np.array([[0,0], [box_size,0], [box_size, box_size], [0, box_size]], dtype=np.float32)

        

        M = cv.getPerspectiveTransform(src_pts, dst_pts)
        warp = cv.warpPerspective(final, M, (box_size, box_size))

        #warp = cv.rotate(warp, cv.ROTATE_180)

        
    #new idea: there is now a blue marker at the bottom of the thermometer
    hsv = cv.cvtColor(warp, cv.COLOR_BGR2HSV)
    #hsv = cv.cvtColor(frame, cv.COLOR_BGR2HSV)

    # Threshold of blue in HSV space
    lower_blue = np.array([100, 100, 0])
    upper_blue = np.array([120, 255, 255]) 
    
    # preparing the mask to overlay
    mask_blue = cv.inRange(hsv, lower_blue, upper_blue)

    # The black region in the mask has the value of 0,
    # so when multiplied with original image removes all non-blue regions
    #warp = cv.bitwise_and(frame,frame, mask = mask_blue) 
    
    
    #find red pixels of original frame
    lower_red_left = np.array([0,100,0])
    upper_red_left = np.array([10,255,255])
    mask_red = cv.inRange(hsv, lower_red_left, upper_red_left)

    
    lower_red_right = np.array([175, 100, 0])
    upper_red_right = np.array([180, 255,255])
    mask_red = mask_red | cv.inRange(hsv, lower_red_right, upper_red_right)
    
    mask_total = mask_blue | mask_red

    #blue_red = cv.bitwise_and(frame,frame, mask = mask_total)
    warp_blue_red = cv.bitwise_and(warp, warp, mask=mask_total)





    
    
    #find angle of red pixels
    warp_red = cv.bitwise_and(warp, warp, mask=mask_red)
    warp_blue = cv.bitwise_and(warp, warp, mask=mask_blue)
     
    #find largest connected components within warp_red, warp_blue

    red_results = contour_finder(warp_red)
    red_contour = red_results[0]
    maxm_red = red_results[1]

    blue_results = contour_finder(warp_blue)
    blue_contour = blue_results[0]
    maxm_blue = blue_results[1]
    
    if maxm_red > 0 and maxm_blue > 0:
        
        
        red_rect = cv.minAreaRect(red_contour)
        red_points = cv.boxPoints(red_rect)
       
        red_area = red_rect[1][0] * red_rect[1][1] #red_rect[1] = (width, height)


        
        blue_rect = cv.minAreaRect(blue_contour)
        blue_points = cv.boxPoints(blue_rect)
        
        blue_area = blue_rect[1][0] * blue_rect[1][1] #blue_rect[1] = (width, height)

  
        if red_area > 1000 and blue_area > 1000:
            
            warp_red = cv.drawContours(warp_red, red_contour, -1, (0, 255, 0), 3)
            warp_blue = cv.drawContours(warp_blue, blue_contour, -1, (0, 255, 0), 3)

            #plotting red rectangle corners for bugtesting
            #for i in range(len(red_points)):
            #    warp_blue_red = cv.circle(warp_blue_red, (int(red_points[i][0]), int(red_points[i][1])), 10, (0,0,255), thickness=-1)

            #plotting blue rectangle corners for bugtesting
            #for i in range(len(blue_points)):
            #    warp_blue_red = cv.circle(warp_blue_red, (int(blue_points[i][0]), int(blue_points[i][1])), 10, (255,0,0), thickness=-1)


            #find short sides of red and blue bounding boxes
            short_red_sides = [] 
            short_blue_sides = []


            red_edge_dict = {}
            red_dist_dict = {}
            #[vertex i, vertex j]: distance squared
            for i in range(len(red_points)):
                for j in range(i, len(red_points)):

                    if i==j:
                        continue
                    
                    redpt1 = red_points[i]
                    redpt2 = red_points[j]

                    red_edge_dict[(i,j)] = [redpt1, redpt2]
                    #includes diagonals
                    
                    temp_dist = (redpt1[0]-redpt2[0])**2 + (redpt1[1]-redpt2[1])**2
                    red_dist_dict[(i,j)] = temp_dist

            #sorting red edges by length, and picking the shortest two
            shortest_red = list(dict(sorted(red_dist_dict.items(), key=lambda item: item[1])[0:2]).keys())
            #print(shortest_red)        
            short_red_midpoints = [list(sum(red_edge_dict[srs])/2) for srs in shortest_red]
            #print(short_red_midpoints)

            blue_edge_dict = {}
            blue_dist_dict = {}
            for i in range(len(blue_points)):
                for j in range(i, len(blue_points)):
                    if i==j:
                        continue

                    bluept1 = blue_points[i]
                    bluept2 = blue_points[j]

                    blue_edge_dict[(i,j)] = [bluept1, bluept2]
                    
                    temp_dist = (bluept1[0] - bluept2[0])**2 + (bluept1[1]-bluept2[1])**2
                    blue_dist_dict[(i,j)] = temp_dist

            #sorting blue edges by length, and picking the shortest two
            shortest_blue = list(dict(sorted(blue_dist_dict.items(), key=lambda item:item[1])[0:2]).keys())
            short_blue_midpoints = [list(sum(blue_edge_dict[srs])/2) for srs in shortest_blue]
            #print(short_blue_midpoints)
            
            

            dists_between = {}
            for n in range(2):
                for m in range(2):

                    #debugging
                    #print("blue midpoint", n, short_blue_midpoints[n], "\n-------------------------\n")
                    #print("red midpoint", m, short_red_midpoints[m],  "\n-------------------------\n")
                    #warp_blue_red = cv.circle(warp_blue_red, tuple([int(x) for x in short_blue_midpoints[n]]), 10, (255,0,0), thickness=-1)
                    #warp_blue_red = cv.circle(warp_blue_red, tuple([int(x) for x in short_red_midpoints[m]]), 10, (0,0,255), thickness=-1)

                    dists_between[(n,m)] = math.sqrt( (short_blue_midpoints[n][0] - short_red_midpoints[m][0])**2 + (short_blue_midpoints[n][1] - short_red_midpoints[m][1])**2 )


                    #print("blue midpoint", n, short_blue_midpoints[n],
                    #      "red midpoint", m, short_red_midpoints[m],  
                    #      "distance between them is", dists_between[(n,m)],"\n-------------------------\n") 
                    pass


            
            shortest_dist_between = list(dict(sorted(dists_between.items(), key=lambda item: item[1])).keys())
            #print(shortest_dist_between)

            n0 = shortest_dist_between[0][0]
            m0 = shortest_dist_between[0][1]

            #bugtesting again. it works!
            #I have found the vertices of the red needle and the blue indicator which form the closest distance between any pairs
            warp_blue_red = cv.circle(warp_blue_red, tuple([int(x) for x in short_blue_midpoints[n0]]), 10, (255,0,0), thickness=-1)
            warp_blue_red = cv.circle(warp_blue_red, tuple([int(x) for x in short_red_midpoints[m0]]), 10, (0,0,255), thickness=-1)

            #because our lists are only two long, we can do this
            n1 = 1-n0
            m1 = 1-m0

            blue_close = tuple([int(x) for x in short_blue_midpoints[n0]])
            blue_far = tuple([int(x) for x in short_blue_midpoints[n1]])

            red_close = tuple([int(x) for x in short_red_midpoints[m0]])
            red_far = tuple([int(x) for x in short_red_midpoints[m1]])
            
            warp_blue_red = cv.arrowedLine(warp_blue_red,
                                           blue_close,
                                           blue_far,
                                           color=(255,0,0),
                                           thickness=10)#, line_type, shift, tipLength)

            warp_blue_red = cv.arrowedLine(warp_blue_red,
                                           red_close,
                                           red_far,
                                           color=(0,0,255),
                                           thickness=10)#, line_type, shift, tipLength)

            blue_vector = [blue_far[0]-blue_close[0], blue_far[1]-blue_close[1]]
            red_vector = [red_far[0]-red_close[0], red_far[1]-red_close[1]]

            blue_norm = math.sqrt( (blue_vector[0]**2) + (blue_vector[1]**2) )
            red_norm = math.sqrt( (red_vector[0]**2) + (red_vector[1]**2) )

            dot_product = ( blue_vector[0]*red_vector[0] ) + ( blue_vector[1]*red_vector[1] )
            norm_dot_product = dot_product / (blue_norm*red_norm)


            cross_product = float(np.cross(red_vector, blue_vector))
            norm_cross_product = cross_product / (blue_norm*red_norm)

            dot_angle = math.acos(norm_dot_product) * 180/math.pi
            cross_angle = math.asin(norm_cross_product) * 180/math.pi 

            out_angle = None
            
            if norm_dot_product < 0:
                #print("dot product is negative")
                #top half of thermometer
                if norm_cross_product > 0:
                    #print("cross product is positive")
                    #print("top right")
                    #use 360 - (angle from dot product)
                    out_angle = 360 - dot_angle
                else:
                    #print("cross product is negative")
                    
                    #print("top left")
                    #use angle from dot product
                    out_angle = dot_angle
                    
            else:
                #print("dot product is positive")
                #bottom half of thermometer
                if norm_cross_product > 0:
                    #print("cross product is positive")
                    #print("bottom right")
                    #this will rarely happen anyway because that would be temps above 100 F
                    #use 360 - (abs(angle from cross product))
                    out_angle = 360 - abs(cross_angle)
                    
                else:
                    #print("cross product is negative")
                    #use angle from dot product
                    #print("bottom left")
                    out_angle = dot_angle
            #print("angle:", out_angle)

            deg_f = fahrenheit(out_angle)
            deg_c = celsius(out_angle)
            
            print(deg_f, "deg Fahrenheit")
            print(deg_c, "deg Celsius")

            print("\n------------------------------------------\n")


    # Display the resulting frame


    cv.imshow('unmodified', frame)
    if maxm > 500:
        cv.imshow('frame', warp_blue_red)

        #cv.imshow('red', warp_red)
        #cv.imshow('blue', warp_blue)

        #cv.imshow('warp', warp)
    if cv.waitKey(1) == ord('q'):
        break
    
# When everything done, release the capture
cap.release()
cv.destroyAllWindows()
