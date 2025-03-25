package common

import (
	"github.com/op/go-logging"
)

var log = logging.MustGetLogger("log")

// ClientConfig Configuration used by the client

type ClientConfig struct {
	ID            string
	ServerAddress string
	Bet           BetRequest
}

// Client Entity that encapsulates how
type Client struct {
	config   ClientConfig
	protocol *Protocol
	running  bool
	bet      BetRequest
}

// NewClient Initializes a new client receiving the configuration
// as a parameter
func NewClient(config ClientConfig) *Client {
	client := &Client{
		config:   config,
		protocol: NewProtocol(config.ServerAddress),
		running:  true,
		bet:      config.Bet,
	}
	return client
}

// Shutdown Gracefully stops the client
func (c *Client) Shutdown() {
	c.protocol.Stop()
}

// StartClientLoop Sends a single bet request to the server
func (c *Client) StartClientLoop() {
	c.protocol.Start()

	err := c.protocol.SendMessage(c.bet)
	if err != nil {
		log.Errorf("action: apuesta_enviada | result: fail | dni: %v | numero: %v | error: %v",
			c.bet.Document,
			c.bet.Number,
			err,
		)
	} else {
		log.Infof("action: apuesta_enviada | result: success | dni: %v | numero: %v",
			c.bet.Document,
			c.bet.Number,
		)
	}

	log.Infof("action: loop_finished | result: success | client_id: %v", c.config.ID)
}
