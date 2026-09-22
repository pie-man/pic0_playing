from picographics import PicoGraphics, DISPLAY_PICO_DISPLAY_2
display = PicoGraphics(display=DISPLAY_PICO_DISPLAY_2, rotate=0)
BLACK = display.create_pen(0, 0, 0)
WHITE = display.create_pen(255, 255, 255)
BLUE = display.create_pen(100, 100, 200)
RED = display.create_pen(200, 50, 50)
GREEN = display.create_pen(50, 200, 50)
MAGENTA = display.create_pen(200, 100, 200)

def plot_lines(display, top_left_x, top_left_y, plot_width, plot_height,
               min_value, value_range, x_start_value, x_range,
               data_block, data_pairs, pen_list=None,
               background_pen=None, clear_plot=True):
    # """ Routine to plot a (multi) line graph in a rectangular area of screen.
    # Requires the x and y coords of the top left corner, plus the width and height.
    # Also requires a minumum value for the x and y scales and the ranges of both values
    # It requires a 'data block', a multi dimensional array where each record (line)
    # is a list of values (at least 2 if intending to plot anything).
    # Finally it requires a list of tuples called "data_pairs" - slightly misnamed as there
    # can be an optional third value in the Tuple.
    # The first value in the tuple is the column of the data block to use for X coordinates.
    # The second value in the tuple is the column of the data block to use for Y coordinates.
    # The third, optional, value should be a 'pen' type for the screen and sets the colour of
    # the line to draw. If not specified, the line will be the same colour as the previous line.
    # If the first tuple doesn't have a third value, the line will be drawn in the same colour
    # as the background... doh.
    # """
    if pen_list is None:
        pen_list = [RED, MAGENTA, BLUE, WHITE] # was passing in the actual 'pen' in data pairs, now passing an index to a list..
    # Clears the rectangle we're going to plot into with a BLACK background
    if background_pen is None:
        display.set_pen(BLACK)
    else:
        display.set_pen(background_pen)
    # If so, should a default line/pen colour also be set ?
    if clear_plot:
        display.rectangle(top_left_x, top_left_y, plot_width, plot_height)
        display.update()
    # Sets a boundary so all the following plotting functions can only draw within that rectangle.
    # This means values outside of the baselines and ranges won't be seen, but equally won't draw
    # over elements outside the 'plot' window.
    display.set_clip(top_left_x, top_left_y, plot_width, plot_height)
    # print(f"Set clip to {top_left_x},{top_left_y} {plot_width} wide, {plot_height} heigh")
    display.set_pen(MAGENTA) # Hardwiring a colour that's not black for lines in case one is not specified.
    for plot_pair in data_pairs: # Loops over data pairs to draw each line requested.
        x_column = plot_pair[0]
        y_column = plot_pair[1]
        if len(plot_pair) > 2:
             display.set_pen(pen_list[plot_pair[3]])
        pixels_per_unit = plot_width / x_range
        vertical_scale = value_range / plot_height
        # print(f"Pixels per unit = {pixels_per_unit}, vertical scale ={vertical_scale}")
        previous_y_value = data_block[0][y_column]
        previous_x_value = data_block[0][x_column]
        # print(f"Previous x,y = {previous_x_value}, {previous_y_value}")
        for readings in data_block[1:]: # skipping the first 'line' as it has been assigned to "Previous value"
            # for the start point of the graph.
            # maybe the keys should be stripped off outside this routine, but I think slices = copies so skipping
            # could be saving memory....
            x_value = readings[x_column]
            y_value = readings[y_column]
            # print(f"Got x,y coords of {x_value},{y_value}")
            if x_value is None or y_value is None:
                print(f"Got x,y coords of {x_value},{y_value} one of which looks dodgy...")
                continue
            x_coord_old = top_left_x + round((previous_x_value - x_start_value) * pixels_per_unit)
            y_coord_old = top_left_y + round(plot_height - ((previous_y_value - min_value) / vertical_scale))
            x_coord_new = top_left_x + round((x_value - x_start_value) * pixels_per_unit)
            y_coord_new = top_left_y + round(plot_height - ((y_value - min_value ) / vertical_scale))
            # print(f"{readings[y_column]} c at a height of {y_coord_new} pixels and {x_coord_new} pixels across")
            display.line(x_coord_old, y_coord_old, x_coord_new, y_coord_new, 2) # line thickness of 2, should it be settable ?
            previous_y_value = y_value
            previous_x_value = x_value
    display.update()
    # time.sleep(0.5)
    display.remove_clip()

"""Demo of a routine which picks one of a preset bunch of tick spacings.
Hopefully it picks the one that get's from a baseline, which is a multiple
of said tickmark to a value greater than the max value indicated, whilst using
the maximum number of tickmarks, within a specified limit, to achieve that"""
def fit_scale_to_range(min_value, max_value, max_divisions, debug_sw=False):
    tickmarks = [0.05, 0.1, 0.2, 0.25, 0.5,
                 1.0, 2.5, 5.0,
                 10, 25, 50]
    range_required = max_value - min_value
    def most_ticks_with(scale_value):
        for multiplier in range (1,max_divisions):
            if multiplier * scale_value >= range_required - (scale_value / 10): # shrink range slightly because of rounding errors.
                if debug_sw:
                    print(f"For tickmark {scale_value}, picking a multiplier of {multiplier} exceeds {range_required}")
                return multiplier
        return 0
    # rearranged = sorted(tickmarks, reverse=True)
    rearranged = sorted(tickmarks, key=most_ticks_with, reverse=True)
    if debug_sw:
        print(f"GOing through re-arranged... : ")
        for tickmark in rearranged:
            print(f"{tickmark:6.2f} : ", end ="")
        print("")
        for tickmark in rearranged:
            print(f"  {most_ticks_with(tickmark):2d}   : ", end = "")
        print("")
    best_tickmark = rearranged[0]
    no_of_ticks = int(round(range_required / best_tickmark))
    for tickmark in rearranged[1:]:
        if most_ticks_with(tickmark) == no_of_ticks:
            if tickmark < best_tickmark:
                best_tickmark = tickmark
        else:
            break
    baseline = (min_value // best_tickmark) * best_tickmark
    if (best_tickmark * no_of_ticks + baseline) < max_value:
        if debug_sw:
            print(f"Activating bat signal : ({best_tickmark} * {no_of_ticks} + {baseline}) < {max_value}")
        no_of_ticks += 1
    if debug_sw:
        print(f"Going with a baseline of {baseline}, {no_of_ticks} times {best_tickmark} should do it..")
    return best_tickmark, baseline, no_of_ticks

def calculate_maximum_y_ticks(axis_height, margin, font=None, scale=None):
    if font is None:
        font = "bitmap8"
    if scale is None:
        font_scale = 2
    font_height = 8 # perhaps a function of font later...
    line_spacing = (font_height * font_scale) + margin
    max_labels = (axis_height + margin) // line_spacing
    return max_labels

def generate_tick_marks(display, top_left_x, top_left_y, plot_width, plot_height,
                        tick_increment, baseline, no_of_ticks,
                        units=None, font=None, scale=None, pen=None):
    """Your guess is as good as mine..."""
    if units is None:
        units = "c"
    if font is None:
        font = "bitmap8"
    if scale is None:
        scale = 2
    if pen is None:
        pen = MAGENTA
    display.set_font(font)
    font_height = 8 * scale
    tickmarks = [f"{baseline + (x * tick_increment)}{units}" for x in range(no_of_ticks)]
    tick_widths = [display.measure_text(text, scale) + 5 for text in tickmarks]
    y_axis_label_width = max(tick_widths)
    tick_spacing = plot_height / no_of_ticks
    display.set_pen(BLACK)
    display.rectangle(top_left_x, top_left_y, y_axis_label_width, plot_height)
    display.set_clip(top_left_x, top_left_y, y_axis_label_width, plot_height)
    display.set_pen(pen)
    for count, (tickmark, width) in enumerate(zip(tickmarks, tick_widths)):
        start_x = round(top_left_x + y_axis_label_width - width)
        start_y = round(top_left_y + plot_height - (count * tick_spacing))
        display.text(tickmark, start_x, start_y - font_height, scale=scale)
        display.line(top_left_x + y_axis_label_width - 4, start_y, top_left_x + y_axis_label_width, start_y, 2)
        # print(f"tickmark {tickmark} @ {start_x}, {start_y}")
    vertical_line_at = top_left_x + y_axis_label_width - 3
    display.line(vertical_line_at, top_left_y, vertical_line_at, top_left_y + plot_height, 2)
    display.update()
    display.remove_clip()
    return y_axis_label_width

def calculate_plot_key_sizes(display, plot_window_width, plot_keys,
                             font=None, key_font_scale=None, margin=None):
    """Using font and fontsize (scale) along with a margin between lines,
    calculate the height required to draw a key and how many names would be on each line."""
    if font is None:
        # font = "bitmap8"
        font_height = 8
    if key_font_scale is None:
        key_font_scale = 2
    if margin is None:
        margin = 3
    space_per_line = (font_height * key_font_scale) + margin
    no_of_keys = len(plot_keys)
    max_key_length = max([display.measure_text(f" {key} - ", key_font_scale) for key in plot_keys])
    # print(f"Max key length is {max_key_length}")
    keys_per_line = no_of_keys
    while max_key_length * keys_per_line > plot_window_width:
        # print(f"{keys_per_line} keys of max length {max_key_length} is {max_key_length * keys_per_line} pixels while plot width is {plot_window_width}")
        keys_per_line -= 1
    if keys_per_line <= 0:
        keys_per_line = 1
    no_of_lines = no_of_keys // keys_per_line
    if no_of_keys % keys_per_line > 0:
        no_of_lines += 1
    # print(f"Got {no_of_keys} keys, gonna print {keys_per_line} keys on {no_of_lines} lines")
    height_required = (no_of_lines * space_per_line) + margin
    if no_of_lines > 3 and key_font_scale > 1:
        key_font_scale -= 1
        if margin > 1:
            margin -= 1
        max_key_length, keys_per_line, height_required, key_font_scale, margin = \
            calculate_plot_key_sizes(display, plot_window_width, plot_keys,
                             font=font, key_font_scale=key_font_scale, margin=margin)
    return max_key_length, keys_per_line, height_required, key_font_scale, margin

def map_key_names_to_data_columns(keys_being_plotted, logfiles_used, log_files_dict,
                                  no_of_colours):
    """Generate a dictionary which maps the name of a logfile to the columns of data within
    that logfile that are being plotted. It also assigns each 'mapping' a number to be used as
    index in a list of pens later which the key name and plot line will be drawn in.
    Each individual 'mapping' for a line includes the x column, the y column, the name
    to use in the key and the index in the colour list all held in a tuple.
    The logfile name then identifies a list of such mappings(tuples) to draw later."""
    plot_key_to_log_column_map = {}
    colours_used = 0
    for log_file_name in logfiles_used:
        plot_key_to_log_column_map[log_file_name] = []
        for count, log_key in enumerate(log_files_dict[log_file_name]["keys"]):
            # print(f"Is it {log_key} ?")
            if log_key in keys_being_plotted:
                colour_to_use = colours_used % no_of_colours
                plot_key_to_log_column_map[log_file_name].append((0, count+1, log_key, colour_to_use)) # x_col hardwired to 0 here...
                colours_used += 1
    return plot_key_to_log_column_map

def draw_key(
        display, key_top_left_x, key_top_left_y, key_width, key_height,
        key_to_log_column_map, keys_per_line, max_key_length,
        x_key_scale, margin, font=None,
        key_colours_list=None, background_pen=None,
        ):
    """The routine designed to clear a portion of screen and draw the key using the mappings created
    in map_key_names_to_data_columns """
    if font is None:
        font = "bitmap8"
    font_height = 8 # replace at some stage with a function based on font name....
    # x_key_scale = 2
    # key_top_left_x = top_left_x
    # key_top_left_y = top_left_y + remaining_plot_window_height + x_axis_height
    # plot_keys = graph_keys
    # no_of_keys = len(plot_keys)
    if key_colours_list is None:
        key_colours_list = [RED, MAGENTA, BLUE, WHITE]
    if background_pen is None:
        background_pen = BLACK

    line_spacing = (font_height * x_key_scale) + margin

    # Clear the background to the Key window
    display.set_pen(background_pen)
    display.rectangle(key_top_left_x, key_top_left_y, key_width, key_height)

    key_no = 0
    y_shift = key_top_left_y + margin
    for data_pairs in key_to_log_column_map.values():
        for data_pair in data_pairs:
            line_no = key_no // keys_per_line
            x_shift = (max_key_length * (key_no % keys_per_line)) + key_top_left_x + (key_width - (keys_per_line * max_key_length)) //2
            y_shift = key_top_left_y + margin + (line_spacing * line_no)
            # print(f"Key_no {key_no} : Key = {data_pair[2]} : Line no {line_no}, x_shift {x_shift}, y_shift {y_shift}")
            display.set_pen(key_colours_list[data_pair[3]])
            display.text(f" {data_pair[2]} - ", x_shift, y_shift, scale=x_key_scale)
            key_no += 1

def calculate_max_and_min_of_scales(logfile_names, log_files_dict, key_to_log_map):
    """A routine to loop through all the logs which are about to be plotted and find the minimum and maximum
    values for the x axis and the y values of all the lines being plotted."""
    min_y = 10000
    max_y = -10000
    min_x = 9999999999
    max_x = -1000000
    line_count = 0
    for log_file_name in logfile_names: # list_o_logs is a list of the logs being plotted (often only one)
        # for 'bits to use' in "this log" for if/when plotting data can come from multiple log files
        current_data_block = log_files_dict[log_file_name]["log"].data
        # current_data_block = log_files_dict[log_file_name]["log"] # dummy input is a plain dict....
        for data_pair in key_to_log_map[log_file_name]:
            x_col = data_pair[0]
            y_col = data_pair[1]
            for line in current_data_block:
                if line[x_col] is not None and line[y_col] is not None:
                    # print(f"Y min/max = {min_y}/{max_y} : X min/max = {min_x}/{max_x}")
                    # print(f"Comparing to : Y {line[y_col]} -=#=- X {line[x_col]}")
                    min_y = min(min_y, line[y_col])
                    max_y = max(max_y, line[y_col])
                    min_x = min(min_x, line[x_col])
                    max_x = max(max_x, line[x_col])
                    line_count += 1
    return min_x, max_x, min_y, max_y, line_count

def plot_graphs(display, top_left_x, top_left_y, plot_window_width, plot_window_height,
                log_files_dict, plot_keys, plot_logs,
                x_axis_marker_scale, y_axis_units, x_axis_markers,
                ):
    """The routine which gets called externally by the logging program.
    This carefully assembles and calculates all the sizes and placements
    for elements of the graph as well as the calls to actually draw those elements within
    a box of size plot_window_width x plot_window_height whose top left corner is specified."""
    # -=# NOTES #=-
    # log_files_dict - The grand list(dictionary, indexed by log filename) of log files (and contents)
    # plot_keys      - The names of the keys to be plotted in this graph. There is currently an
    #                  assumption that each key name only appears once in all the log files.
    # plot_logs.     - Each graph has a list of the name(s) of specific log file(s) to data to use is in.
    
    line_colours = [RED, MAGENTA, BLUE, WHITE] # ultimately, this should possibly be passed in.
    # partly because it would reduce the requirement for this module to import display but also because
    # it would allow every graph to use it's own unique pallet (hold on to yer lunch - could get garish)
    # -=# END of NOTES #=-

    # Step zero : Work out the columns of the Y values in each of the logs...
    # I'm not a C programmer, I'd just labelled steps 1 through 8 before I realised I needed to do this early on...
    plot_key_to_log_column_map = map_key_names_to_data_columns(plot_keys,
                                                               plot_logs,
                                                               log_files_dict,
                                                               len(line_colours))
    
    # Step one : Work out the bounds of all the lines to be printed:
    #               That is the minumim value of all lines
    #               The Maximum value of all lines to be drawn (and thus perhaps the range)
    min_x, max_x, min_y, max_y, records = calculate_max_and_min_of_scales(plot_logs, log_files_dict, plot_key_to_log_column_map)
    x_range = max_x - min_x

    if records < 4:
        print(f"With {records} useful records, there is insufficient data to plot a graph.")
        return

    # Step two : work out if there's a key, where it sits and how much plot area it takes up
    #               Assumption may be, it's at the bottom and takes one or two text lines height
    #               from the plot window.
    max_key_length, keys_per_line, key_height, key_font_scale, key_margin = \
            calculate_plot_key_sizes(display, plot_window_width, plot_keys)
    remaining_plot_window_height = plot_window_height - key_height

    # Step three : decide on X axis height, we can't draw it until we know Y axis width
    # Hopefully we can 'guess' this based on font height and a bit of gap to put some ticks in..
    x_axis_height = 25
    remaining_plot_window_height = remaining_plot_window_height - x_axis_height

    # Step four: Work out number of tickmarks we can write...
    #              That's a function of font (text height), scale, minimum gap (blank space in pixels)
    #              and the amount of plot window height we have left after a key and x axis are drawn..
    tick_margin = 10 # The minimum numer of pixels betwen tick labels if maximum_tick_limit is used.
    maximum_tick_limit = calculate_maximum_y_ticks(remaining_plot_window_height, tick_margin)

    # Step five: Work out how many tick marks, and what thier spacing, in terms of the y values, is.
    tickmark_spacing, baseline_value, no_of_ticks = fit_scale_to_range(min_y, max_y, maximum_tick_limit)
    plot_range = (tickmark_spacing * no_of_ticks)

    # Step six: Draw the y axis and lables and get back how wide it is
    y_axis_label_width = generate_tick_marks(display, top_left_x, top_left_y,
                                             plot_window_width, remaining_plot_window_height,
                                             tickmark_spacing, baseline_value, no_of_ticks,
                                             pen=BLUE, units="c")

    # Step seven: Draw the X axis labels now we can shift it over for y_axis_label_width
    text = "Look Ma, an X axis label"
    margin = 6
    x_label_scale = 2
    x_axis_top_left_x = top_left_x
    x_axis_top_left_y = top_left_y + remaining_plot_window_height
    plot_window_width = plot_window_width
    x_axis_width = plot_window_width - y_axis_label_width
    display.set_pen(BLACK)
    display.rectangle(x_axis_top_left_x, x_axis_top_left_y, plot_window_width, x_axis_height)
    display.set_pen(GREEN)
    display.line(x_axis_top_left_x + y_axis_label_width, x_axis_top_left_y + 3, plot_window_width, x_axis_top_left_y + 3)
    tick_count = 6
    tick_gap = x_axis_width / (tick_count +1)
    for tick in range(1,tick_count + 1):
        x_point = round(tick * tick_gap) + x_axis_top_left_x + y_axis_label_width
        display.line(x_point, x_axis_top_left_y, x_point, x_axis_top_left_y + 4)
    space_left = max(y_axis_label_width, (y_axis_label_width + plot_window_width - display.measure_text(text, x_label_scale)) // 2)
    text_start = x_axis_top_left_x + space_left
    display.text(text, text_start, x_axis_top_left_y + margin )
    display.update()

    # Step eight: Draw the key daddio....
    key_top_left_x = top_left_x
    key_top_left_y = top_left_y + remaining_plot_window_height + x_axis_height
    # key_scale = 2
    draw_key(
        display, key_top_left_x, key_top_left_y, plot_window_width, key_height,
        plot_key_to_log_column_map, keys_per_line, max_key_length,
        key_font_scale, key_margin, font=None,
        key_colours_list=None, background_pen=None,
        )

    # Step nine: Draw the danged lines baby, draw the danged lines....
    clear_plot_window = True
    for log_file_name, data_pairs in plot_key_to_log_column_map.items():
        current_data_block = log_files_dict[log_file_name]["log"].data
        # current_data_block = log_files_dict[log_file_name]["log"] # dummy input is a plain dict....
        plot_lines(display, top_left_x + y_axis_label_width, top_left_y, plot_window_width - y_axis_label_width, remaining_plot_window_height,
                baseline_value, plot_range,
                min_x, x_range,
                current_data_block, data_pairs,
                clear_plot=clear_plot_window)
        if clear_plot_window:
            clear_plot_window = False # basically only clear the window on the 1st call when looping through logfiles
    display.update()
    return