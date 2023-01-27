package main

import (
	"context"
	"crypto/hmac"
	"crypto/rand"
	"encoding/base64"
	"fmt"
	"log"
	"math"
	"net/http"
	"os"
	"strconv"
	"strings"
	"time"

	ratelimit "github.com/JGLTechnologies/gin-rate-limit"
	"github.com/fernet/fernet-go"
	"github.com/gin-gonic/gin"
	"github.com/joho/godotenv"
	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"
)

// Database collections
var users *mongo.Collection
var licenses *mongo.Collection

// Database record structure
type User struct {
	Username    string
	Password    string
	HardwareID  string `bson:"hardware_id"`
	Resets      int    `bson:"hwid_resets"`
	Note        string
	DateCreated string `bson:"date_created"`
}

type License struct {
	Key         string `bson:"license"`
	DateCreated string `bson:"date_created"`
}

// Load the values of the API config
func loadConfig() {
	err := godotenv.Load("configuration/config.env")
	if err != nil {
		log.Fatal("Unable to load configuration: ", err)
	}
}

// Connect to the MongoDB database
func connectToDatabase() {
	// Configure database connection
	serverOptions := options.ServerAPI(options.ServerAPIVersion1)
	databaseOptions := options.Client().
		ApplyURI(os.Getenv("database_uri")).
		SetServerAPIOptions(serverOptions)

	// Connect to database
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	cluster, err := mongo.Connect(ctx, databaseOptions)
	if err != nil {
		log.Fatal("Unable to connect to database: ", err)
	}

	// Load collections from database
	users = cluster.Database("authentication").Collection("users")
	licenses = cluster.Database("authentication").Collection("licenses")
}

// Access request IP addresses for ratelimiting
func getClientIP(ctx *gin.Context) string {
	return ctx.ClientIP()
}

// Display 429 error when ratelimiting clients
func ratelimitError(ctx *gin.Context, info ratelimit.Info) {
	ctx.String(429, "Too many requests. Try again in "+time.Until(info.ResetTime).String())
}

// Encrypt API responses
func encrypt(content string) string {
	// Load encryption key and encrypt content
	secret := fernet.MustDecodeKeys(os.Getenv("encryption_key"))
	encrypted, err := fernet.EncryptAndSign([]byte(content), secret[0])
	if err != nil {
		log.Fatal("Unable to encrypt message: ", err)
	}

	// Convert byte array to string and return
	return string(encrypted)
}

// Generate a license key
func generateLicense() (string, string, error) {
	// Generate random seed cryptographically
	buffer := make([]byte, int(math.Ceil(float64(18)/float64(1.33333333333))))
	_, err := rand.Read(buffer)
	if err != nil {
		return "", "", err
	}

	// Convert to string and standardize case
	seed := base64.RawURLEncoding.EncodeToString(buffer)
	licenseKey := strings.ToUpper(seed[:18])
	dateCreated := time.Now().Format("01/02/2006")

	// Add license to database
	_, err = licenses.InsertOne(
		context.TODO(),
		License{Key: licenseKey, DateCreated: dateCreated},
	)

	if err != nil {
		return "", "", err
	}

	return licenseKey, dateCreated, nil
}

// Display API status at the root
func root(ctx *gin.Context) {
	ctx.JSON(http.StatusOK, gin.H{"status": "online"})
}

// Validate a user login attempt
func loginAccount(ctx *gin.Context) {
	// Fetch query parameters parameters
	username := ctx.Query("username")
	password := ctx.Query("password")
	hwid := ctx.Query("hwid")

	// Find account in database
	filter := bson.D{
		{Key: "username", Value: username},
		{Key: "password", Value: password},
	}

	var result User
	err := users.FindOne(context.TODO(), filter).Decode(&result)

	// Check if account was found
	if err == mongo.ErrNoDocuments {
		ctx.JSON(http.StatusNotFound, gin.H{"status": encrypt("Account not found")})
		return
	} else if err != nil {
		log.Print("Unable to search for account: ", err)
		ctx.Status(http.StatusInternalServerError)
		return
	}

	// Check if HWID is not already set in database
	if result.HardwareID == "" {
		_, err := users.UpdateOne(context.TODO(), filter, bson.D{
			{Key: "$set", Value: bson.D{{Key: "hardware_id", Value: hwid}}},
		})
		if err != nil {
			log.Print("Unable to update account HWID: ", err)
			ctx.Status(http.StatusInternalServerError)
			return
		}
	} else if !hmac.Equal([]byte(hwid), []byte(result.HardwareID)) {
		// Deny if attempt HWID and database HWID do not match
		ctx.JSON(http.StatusUnauthorized, gin.H{"status": encrypt("Unauthorized HWID")})
		return
	}

	// Allow successful login
	ctx.JSON(http.StatusOK, gin.H{"status": encrypt("Successfully logged in")})
}

// Register a new user account
func createAccount(ctx *gin.Context) {
	// Fetch query parameters
	username := ctx.Query("username")
	password := ctx.Query("password")
	licenseKey := ctx.Query("license")

	// Deny if username already used
	filter := bson.D{{Key: "username", Value: username}}

	var result User
	err := users.FindOne(context.TODO(), filter).Decode(&result)

	if err != mongo.ErrNoDocuments {
		ctx.JSON(http.StatusBadRequest, gin.H{"status": encrypt("Username already exists")})
		return
	}

	// Deny if license does not exist
	licenseKey = strings.ToUpper(licenseKey)
	filter = bson.D{{Key: "license", Value: licenseKey}}

	var license License
	err = licenses.FindOne(context.TODO(), filter).Decode(&license)

	if err == mongo.ErrNoDocuments {
		ctx.JSON(http.StatusBadRequest, gin.H{"status": encrypt("License does not exist")})
		return
	}

	// Delete license from database upon validation
	_, err = licenses.DeleteOne(context.TODO(), filter)

	if err != nil {
		log.Print("Unable to delete license: ", err)
		ctx.Status(http.StatusInternalServerError)
		return
	}

	// Create user account if all conditions met
	_, err = users.InsertOne(
		context.TODO(),
		User{
			Username:    username,
			Password:    password,
			HardwareID:  "",
			Resets:      0,
			Note:        "",
			DateCreated: time.Now().Format("01/02/2006"),
		},
	)

	if err != nil {
		log.Print("Unable to create new account: ", err)
		ctx.Status(http.StatusInternalServerError)
		return
	}

	// Signal successful account creation
	ctx.JSON(http.StatusCreated, gin.H{"status": encrypt("Successfully registered account")})
}

// Fetch user account data by username
func fetchAccount(ctx *gin.Context) {
	// Fetch query parameters
	username := ctx.Query("username")

	// Find account in database
	filter := bson.D{{Key: "username", Value: username}}

	var result User
	err := users.FindOne(context.TODO(), filter).Decode(&result)

	// Check if account was found
	if err == mongo.ErrNoDocuments {
		ctx.JSON(http.StatusNotFound, gin.H{"status": encrypt("Account not found")})
		return
	} else if err != nil {
		log.Print("Unable to search for account: ", err)
		ctx.Status(http.StatusInternalServerError)
		return
	}

	// Return account data
	ctx.JSON(http.StatusOK, gin.H{
		"username":     encrypt(result.Username),
		"password":     encrypt(result.Password),
		"hwid_resets":  encrypt(strconv.Itoa(result.Resets)),
		"note":         encrypt(result.Note),
		"date_created": encrypt(result.DateCreated),
	})
}

// Delete a user account by username
func deleteAccount(ctx *gin.Context) {
	// Fetch query parameters
	username := ctx.Query("username")

	// Find account in database
	filter := bson.D{{Key: "username", Value: username}}

	var result User
	err := users.FindOne(context.TODO(), filter).Decode(&result)

	// Check if account was found
	if err == mongo.ErrNoDocuments {
		ctx.JSON(http.StatusNotFound, gin.H{"status": encrypt("Account not found")})
		return
	} else if err != nil {
		log.Print("Unable to search for account: ", err)
		ctx.Status(http.StatusInternalServerError)
		return
	}

	// Delete account from database
	_, err = users.DeleteOne(context.TODO(), filter)

	if err != nil {
		log.Print("Unable to delete account: ", err)
		ctx.Status(http.StatusInternalServerError)
		return
	}

	// Signal successful account deletion
	ctx.JSON(http.StatusOK, gin.H{"status": encrypt("Successfully deleted account")})
}

// Fetch user account by username and reset its HWID
func resetAccountHWID(ctx *gin.Context) {
	// Fetch query parameters
	username := ctx.Query("username")

	// Find account in database
	filter := bson.D{{Key: "username", Value: username}}

	var result User
	err := users.FindOne(context.TODO(), filter).Decode(&result)

	// Check if account was found
	if err == mongo.ErrNoDocuments {
		ctx.JSON(http.StatusNotFound, gin.H{"status": encrypt("Account not found")})
		return
	} else if err != nil {
		log.Print("Unable to search for account: ", err)
		ctx.Status(http.StatusInternalServerError)
		return
	}

	// Reset account HWID
	_, err = users.UpdateOne(context.TODO(), filter, bson.D{
		{Key: "$set", Value: bson.D{
			{Key: "hardware_id", Value: ""},
			{Key: "hwid_resets", Value: (result.Resets + 1)},
		}},
	})

	if err != nil {
		log.Print("Unable to update account HWID: ", err)
		ctx.Status(http.StatusInternalServerError)
		return
	}

	// Signal successful HWID reset
	ctx.JSON(http.StatusOK, gin.H{"status": encrypt("Successfully reset HWID")})
}

// Fetch user account by username and change its password
func resetAccountPassword(ctx *gin.Context) {
	// Fetch query parameters
	username := ctx.Query("username")
	newPassword := ctx.Query("password")

	// Find account in database
	filter := bson.D{{Key: "username", Value: username}}

	var result User
	err := users.FindOne(context.TODO(), filter).Decode(&result)

	// Check if account was found
	if err == mongo.ErrNoDocuments {
		ctx.JSON(http.StatusNotFound, gin.H{"status": encrypt("Account not found")})
		return
	} else if err != nil {
		log.Print("Unable to search for account: ", err)
		ctx.Status(http.StatusInternalServerError)
		return
	}

	// Change account password
	_, err = users.UpdateOne(context.TODO(), filter, bson.D{
		{Key: "$set", Value: bson.D{{Key: "password", Value: newPassword}}},
	})

	if err != nil {
		log.Print("Unable to update account password: ", err)
		ctx.Status(http.StatusInternalServerError)
		return
	}

	// Signal successful password change
	ctx.JSON(http.StatusOK, gin.H{"status": encrypt("Successfully changed password")})
}

// Fetch user account by username and change its note
func changeAccountNote(ctx *gin.Context) {
	// Fetch query parameters
	username := ctx.Query("username")
	newNote := ctx.Query("note")

	// Find account in database
	filter := bson.D{{Key: "username", Value: username}}

	var result User
	err := users.FindOne(context.TODO(), filter).Decode(&result)

	// Check if account was found
	if err == mongo.ErrNoDocuments {
		ctx.JSON(http.StatusNotFound, gin.H{"status": encrypt("Account not found")})
		return
	} else if err != nil {
		log.Print("Unable to search for account: ", err)
		ctx.Status(http.StatusInternalServerError)
		return
	}

	// Change account note
	_, err = users.UpdateOne(context.TODO(), filter, bson.D{
		{Key: "$set", Value: bson.D{{Key: "note", Value: newNote}}},
	})

	if err != nil {
		log.Print("Unable to change account note: ", err)
		ctx.Status(http.StatusInternalServerError)
		return
	}

	// Signal successful note change
	ctx.JSON(http.StatusOK, gin.H{"status": encrypt("Successfully changed note")})
}

// Generate a license key for user registration
func createLicense(ctx *gin.Context) {
	// Generate new license key and add to database
	licenseKey, dateCreated, err := generateLicense()
	if err != nil {
		log.Print("Unable to generate license: ", err)
		ctx.Status(http.StatusInternalServerError)
		return
	}

	// Return new license data
	ctx.JSON(http.StatusCreated, gin.H{
		"license":      encrypt(licenseKey),
		"date_created": encrypt(dateCreated),
	})
}

// Summarize database collection totals
func stats(ctx *gin.Context) {
	// Calculate user account totals
	userCount, err := users.EstimatedDocumentCount(context.TODO())
	if err != nil {
		log.Print("Unable to estimate user collection totals: ", err)
		ctx.Status(http.StatusInternalServerError)
		return
	}

	// Calculate license totals
	licenseCount, err := licenses.EstimatedDocumentCount(context.TODO())
	if err != nil {
		log.Print("Unable to estimate license collection totals: ", err)
		ctx.Status(http.StatusInternalServerError)
		return
	}

	// Return collection totals
	ctx.JSON(http.StatusOK, gin.H{
		"user_count":    userCount,
		"license_count": licenseCount,
	})
}

// Load data and start the API
func main() {
	// Load config and connect to database
	loadConfig()
	connectToDatabase()

	// Initialize API router
	gin.SetMode(gin.ReleaseMode)
	router := gin.Default()
	fmt.Println("[GIN] AuthPlus API listening on ", os.Getenv("api_url"))

	// Set up ratelimit cache and middleware
	store := ratelimit.InMemoryStore(&ratelimit.InMemoryOptions{
		Rate:  time.Minute,
		Limit: 15,
	})

	middleware := ratelimit.RateLimiter(store, &ratelimit.Options{
		ErrorHandler: ratelimitError,
		KeyFunc:      getClientIP,
	})

	router.Use(middleware)

	// Set up HTTP basic auth groups
	admin := router.Group("/", gin.BasicAuth(gin.Accounts{
		"ADMIN": os.Getenv("admin_password"),
	}))

	client := router.Group("/", gin.BasicAuth(gin.Accounts{
		"CLIENT": os.Getenv("client_password"),
	}))

	// Public API routes
	router.GET("/", root)
	router.GET("/stats", stats)

	// Client API routes
	client.POST("/account/login", loginAccount)

	// Admin API routes
	admin.POST("/account/create", createAccount)
	admin.GET("/account/fetch", fetchAccount)
	admin.DELETE("/account/delete", deleteAccount)
	admin.PATCH("/account/hwid", resetAccountHWID)
	admin.PATCH("/account/password", resetAccountPassword)
	admin.PATCH("/account/note", changeAccountNote)
	admin.POST("/license/create", createLicense)

	// Run Gin API router
	err := router.Run(os.Getenv("api_url"))
	if err != nil {
		log.Fatal(err)
	}
}
