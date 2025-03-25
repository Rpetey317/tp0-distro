package common

import (
	"bufio"
	"os"
	"strconv"
	"strings"
	"time"

	"github.com/op/go-logging"
)

var log = logging.MustGetLogger("log")

// ClientConfig Configuration used by the client

type ClientConfig struct {
	ID            string
	ServerAddress string
	BetsFile      string
}

// Client Entity that encapsulates how
type Client struct {
	config    ClientConfig
	protocol  *Protocol
	running   bool
	bets_file string
}

func readBetsFile(bets_file string) BetRequestBatch {
	var bet_requests []BetRequest

	// Open and read the bets file
	file, err := os.Open(bets_file)
	if err != nil {
		log.Errorf("action: read_bets_file | result: fail | error: %v", err)
		return BetRequestBatch{Bets: bet_requests}
	}
	defer file.Close()

	// Create CSV reader
	scanner := bufio.NewScanner(file)

	// Read each line and create bet requests
	for scanner.Scan() {
		line := scanner.Text()
		record := strings.Split(line, ",")
		if len(record) != 5 {
			log.Errorf("action: read_bets_file | result: fail | error: invalid record length")
			continue
		}

		// Parse fields from CSV
		// Format: FirstName,LastName,Document,BirthDate,Number
		name := record[0]
		surname := record[1]
		document, err := strconv.Atoi(record[2])
		if err != nil {
			log.Errorf("action: read_bets_file | result: fail | error: %v", err)
			continue
		}
		birthdate, err := time.Parse("2006-01-02", record[3])
		if err != nil {
			log.Errorf("action: read_bets_file | result: fail | error: %v", err)
			continue
		}
		number, err := strconv.Atoi(record[4])
		if err != nil {
			log.Errorf("action: read_bets_file | result: fail | error: %v", err)
			continue
		}

		// Create bet request
		bet_request := BetRequest{
			Name:      name,
			Surname:   surname,
			Birthdate: birthdate,
			Document:  document,
			Number:    number,
		}

		bet_requests = append(bet_requests, bet_request)
	}

	return BetRequestBatch{Bets: bet_requests}
}

// NewClient Initializes a new client receiving the configuration
// as a parameter
func NewClient(config ClientConfig) *Client {
	client := &Client{
		config:    config,
		protocol:  NewProtocol(config.ServerAddress),
		running:   true,
		bets_file: config.BetsFile,
	}
	return client
}

// Shutdown Gracefully stops the client
func (c *Client) Shutdown() {
	c.protocol.Stop()
}

// StartClientLoop Sends a single bet request to the server
func (c *Client) StartClientLoop() {

	bet_requests := readBetsFile(c.bets_file)

	c.protocol.Start()
	defer c.protocol.Stop()

	err := c.protocol.SendBetRequestBatch(bet_requests)
	if err != nil {
		log.Errorf("action: send_bet_request_batch | result: fail | error: %v", err)
	}

	log.Infof("action: loop_finished | result: success | client_id: %v", c.config.ID)
}
