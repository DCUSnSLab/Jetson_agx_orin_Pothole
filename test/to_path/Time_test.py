import time

# Get the current time in seconds with fractions
current_time = time.time()

# Extract seconds and milliseconds
seconds = int(current_time)
milliseconds = int((current_time - seconds) * 1000)

# Format the time string including minutes, seconds, and milliseconds with three decimal places
formatted_time = time.strftime("%Y-%m-%d_%H:%M:%S.{:03d}", time.localtime(seconds))

# Include the milliseconds in the formatted string
formatted_time_with_milliseconds = formatted_time.format(milliseconds)

print(formatted_time_with_milliseconds)