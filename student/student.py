from typing import List

# Adapted from code by Zach Peats

# ======================================================================================================================
# Do not touch the client message class!
# ======================================================================================================================


class ClientMessage:
	"""
	This class will be filled out and passed to student_entrypoint for your algorithm.
	"""
	total_seconds_elapsed: float	  # The number of simulated seconds elapsed in this test
	previous_throughput: float		  # The measured throughput for the previous chunk in kB/s

	buffer_current_fill: float		  # The number of kB currently in the client buffer
	buffer_seconds_per_chunk: float     # Number of seconds that it takes the client to watch a chunk. Every
										# buffer_seconds_per_chunk, a chunk is consumed from the client buffer.
	buffer_seconds_until_empty: float   # The number of seconds of video left in the client buffer. A chunk must
										# be finished downloading before this time to avoid a rebuffer event.

	# The quality bitrates are formatted as follows:
	#
	#   quality_levels is an integer reflecting the # of quality levels you may choose from.
	#
	#   quality_bitrates is a list of floats specifying the number of kilobytes the upcoming chunk is at each quality
	#   level. It always scales linearly with quality level.
	#       quality_bitrates[0] = kB cost for quality level 0
	#       quality_bitrates[1] = kB cost for quality level 1
	#       ...
	#
	#   upcoming_quality_bitrates is a list of quality_bitrates for future chunks. Each entry is a list of
	#   quality_bitrates that will be used for an upcoming chunk. Use this for algorithms that look forward multiple
	#   chunks in the future. Will shrink and eventually become empty as streaming approaches the end of the video.
	#       upcoming_quality_bitrates[0]: Will be used for quality_bitrates in the next student_entrypoint call
	#       upcoming_quality_bitrates[1]: Will be used for quality_bitrates in the student_entrypoint call after that
	#       ...
	#
	quality_levels: int
	quality_bitrates: List[float]
	upcoming_quality_bitrates: List[List[float]]

	# You may use these to tune your algorithm to each user case!
	#
	#   User Quality of Experience =    (Average chunk quality) * (Quality Coefficient) +
	#                                   -(Number of changes in chunk quality) * (Variation Coefficient)
	#                                   -(Amount of time spent rebuffering) * (Rebuffering Coefficient)
	#
	#   *QoE is then divided by total number of chunks
	#
	quality_coefficient: float
	variation_coefficient: float
	rebuffering_coefficient: float
# ======================================================================================================================


# Your helper functions, variables, classes here. You may also write initialization routines to be called
# when this script is first imported and anything else you wish.


def student_entrypoint(client_message: ClientMessage):
	"""
	Your mission, if you choose to accept it, is to build an algorithm for chunk bitrate selection that provides
	the best possible experience for users streaming from your service.

	Construct an algorithm below that selects a quality for a new chunk given the parameters in ClientMessage. Feel
	free to create any helper function, variables, or classes as you wish.

	Simulation does ~NOT~ run in real time. The code you write can be as slow and complicated as you wish without
	penalizing your results. Focus on picking good qualities!

	Args:
		client_message : ClientMessage holding the parameters for this chunk and current client state.

	:return: float Your quality choice. Must be one in the range [0 ... quality_levels] inclusive.
	"""
	return MPC(client_message)


# ======================================================================================================================
#
# Tanner's code below!
#
# ======================================================================================================================

def HYB(client_message: ClientMessage):
	""" Quick and dirty HYB implementation. Uses the previous chunk throughput as a current throughput prediction. """
	cm = client_message
	if cm.previous_throughput == 0:
		return 0
	valid_throughputs = [
		i for i in range(cm.quality_levels)
		if cm.quality_bitrates[i] / cm.previous_throughput < cm.buffer_seconds_until_empty
	]
	return max(valid_throughputs) if valid_throughputs else 0


# Params for MPC
LOOKAHEAD = 5  # Lookahead 5 chunks
prev_choice = None  # Used to hold previous quality level


def MPC(client_message: ClientMessage):
	"""
	MPC algorithm from https://dl.acm.org/doi/pdf/10.1145/2785956.2787486
	Instead of solving optimization problem, uses an exhaustive search of all possibilities.
	Skips startup phase.
	Uses previous chunk throughput for current block
	"""
	global prev_choice

	def qos_predict(upcoming_quality_bitrates, seconds_in_buffer, throughput, last_quality):
		# Default to zero score for no options
		if not upcoming_quality_bitrates:
			return 0, []
		# Choose low quality if no throughput prediction
		if throughput == 0:
			return 0, [0]
		# Get bitrate options and initialize best calculated QoS and bitrate choices
		bitrate_options = upcoming_quality_bitrates[0]
		best_qos, best_choices = -1000000000, [0]
		# Brute force enumeration of all possibilites
		for i in range(len(bitrate_options)):
			# Calculate parameters
			download_time = bitrate_options[i] / throughput
			rebuff_time = max(download_time - seconds_in_buffer, 0)

			# Find best QOS for the rest of the chunks assuming we picked i
			qos, choices = \
				qos_predict(upcoming_quality_bitrates[1:], max(seconds_in_buffer - download_time, 0), throughput, i)

			# Calculate QOS
			qos =   \
				qos + client_message.quality_coefficient * i - \
				(client_message.variation_coefficient if last_quality is not None and i != last_quality else 0) - \
				client_message.rebuffering_coefficient * rebuff_time

			# If this is better than the best, this is the best
			if qos > best_qos:
				best_qos = qos
				best_choices = [i] + choices

		# Return the best calculated QoS and quality choices
		return best_qos, best_choices

	pred_qos, chosen_qualities = qos_predict(
		[client_message.quality_bitrates] +
		client_message.upcoming_quality_bitrates[:min(len(client_message.upcoming_quality_bitrates), LOOKAHEAD)],
		client_message.buffer_seconds_until_empty,
		client_message.previous_throughput,
		prev_choice
	)
	print(f'Predicted {chosen_qualities} with a QoS of {pred_qos}')
	prev_choice = chosen_qualities[0]
	return chosen_qualities[0]
