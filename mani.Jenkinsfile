pipeline {
    agent any

    environment {
        def myString = "Hello World"
        def myNumber = 10
        def myBool = true

    }

    stages {
        stage ('Demo'){
            steps {
                echo "myString : ${myString}"
                echo "myNumber : ${myNumber}"
                echo "myBool : ${myBool}"
            }
        }
    }
}