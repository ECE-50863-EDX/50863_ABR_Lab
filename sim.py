import configparser
from typing import Tuple, List, Type
from Classes import SimBuffer, NetworkTrace, Scorecard
import sys
from student import student

# Adapted from simulator.py written by Zach Peats

# ======================================================================================================================
# CONFIG PARAMETERS
# ======================================================================================================================
DESCRIPTION_HEADING = 'description'
DESCRIPTION		 = 'description'

VIDEO_HEADING	   = 'video'
CHUNK_LENGTH		= 'chunk_length'
CLIENT_BUFF_SIZE	= 'client_buffer_size'

QUALITY_HEADING	 = 'quality'
QUALITY_LEVELS	  = 'quality_levels'
KILOBYTES_PER_LEVEL = 'kilobytes_per_level'
QUAL_COEF		   = 'quality_coefficient'
BUF_COEF			= 'rebuffering_coefficient'
SWITCH_COEF		 = 'variation_coefficient'

THROUGHPUT_HEADING  = 'throughput'

CHUNK_COST_HEADING  = 'chunk_costs'
CHUNK_COSTS		 = 'chunk_costs'


def read_test(config_path: str):
	"""
	Reads and loads parameters from config_path
	Args:
		config_path : .ini file to read
	:return:
		Tuple containing the NetworkTrace, Scorecard, SimBuffer, a list of chunk quality bitrates,
		and the chunk duration. The chunk quality options are formatted as a list of lists. e.g.
		chunk_qualities[3][1] = number of bytes for chunk index 3, quality index 1.
	"""
	try:
		print(f'\nLoading test file {config_path}.')
		cfg = configparser.RawConfigParser(allow_no_value=True, inline_comment_prefixes='#')
		cfg.read(config_path)

		description = cfg.get(DESCRIPTION_HEADING, DESCRIPTION)
		print(f'\tDescription: {description.strip()}')

		chunk_length = float(cfg.get(VIDEO_HEADING, CHUNK_LENGTH))
		print(f'\tLoaded chunk length {chunk_length} seconds seconds.')

		quality_levels = int(cfg.get(QUALITY_HEADING, QUALITY_LEVELS))
		kilobytes_per_level = float(cfg.get(QUALITY_HEADING, KILOBYTES_PER_LEVEL))
		print(f'\tLoaded {quality_levels} quality levels available, {kilobytes_per_level}kB/level.')

		quality_coefficient = float(cfg.get(QUALITY_HEADING, QUAL_COEF))
		rebuffering_coefficient = float(cfg.get(QUALITY_HEADING, BUF_COEF))
		variation_coefficient = float(cfg.get(QUALITY_HEADING, SWITCH_COEF))
		print(  f'\tLoaded {quality_coefficient} quality coefficient,'
				f' {rebuffering_coefficient} rebuffering coefficient,'
				f' {variation_coefficient} variation coefficient.')

		throughputs = dict(cfg.items(THROUGHPUT_HEADING))
		throughputs = [(float(time), float(throughput)) for time, throughput in throughputs.items()]
		print(f'\tLoaded {len(throughputs)} different throughputs.')

		chunks = cfg.get(CHUNK_COST_HEADING, CHUNK_COSTS)
		chunks = list(float(x) for x in chunks.split(',') if x.strip())
		chunk_qualities = [[c * i * kilobytes_per_level for i in range(1, quality_levels + 1)] for c in chunks]
		print(f'\tLoaded {len(chunks)} chunks. Total video length is {len(chunks) * chunk_length} seconds.')

		trace = NetworkTrace.NetworkTrace(throughputs)
		logger = Scorecard.Scorecard(quality_coefficient, rebuffering_coefficient, variation_coefficient, chunk_length)
		buffer = SimBuffer.SimBuffer(chunk_length)

		print(f'\tDone reading config!\n')

		return trace, logger, buffer, chunk_qualities, chunk_length

	except:
		print('Exception reading config file!')
		import traceback
		traceback.print_exc()
		exit()


# ======================================================================================================================
# MAIN
# ======================================================================================================================
if __name__ == "__main__":

	assert len(sys.argv) >= 2, f'Proper usage: python3 {sys.argv[0]} [config_file] [-v --verbose]'

	verbose = "-v" in sys.argv or "--verbose" in sys.argv

	trace, logger, buffer, chunk_qualities, chunk_length = read_test(sys.argv[1])

	current_time = 0
	prev_throughput = 0

	#Communication loop with student (for all chunks):

	for chunknum in range(len(chunk_qualities)):
		#
		# Set up message for student
		message = student.ClientMessage()
		message.total_seconds_elapsed = current_time
		message.previous_throughput = prev_throughput
		# Buffer
		message.buffer_current_fill = buffer.get_occupancy()
		message.buffer_seconds_per_chunk = chunk_length
		message.buffer_seconds_until_empty = buffer.seconds_left
		# Video
		message.quality_levels = len(chunk_qualities[chunknum])
		message.quality_bitrates = chunk_qualities[chunknum]
		message.upcoming_quality_bitrates = chunk_qualities[chunknum+1:] if chunknum < len(chunk_qualities) - 1 else []
		# Quality
		message.quality_coefficient = logger.quality_coeff
		message.rebuffering_coefficient = logger.rebuffer_coeff
		message.variation_coefficient = logger.switch_coeff

		# Call student algorithm
		quality = student.student_entrypoint(message)
		if quality < 0 or quality >= len(chunk_qualities[chunknum]) or not isinstance(quality, int):
			print("Student returned invalid quality, exiting")
			break
		chosen_bitrate = chunk_qualities[chunknum][quality]

		# Simulate download
		time_elapsed = trace.simulate_download_from_time(current_time, chosen_bitrate)
		rebuff_time = buffer.sim_chunk_download(chosen_bitrate, time_elapsed)

		# Update state variables and log
		prev_throughput = chosen_bitrate / time_elapsed
		current_time += time_elapsed
		logger.log_bitrate_choice(current_time, quality, chosen_bitrate)
		logger.log_rebuffer(current_time - rebuff_time, rebuff_time, chunknum)

	logger.output_results(verbose=verbose)