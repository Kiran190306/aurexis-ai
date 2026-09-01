package com.jarvis.ai.ui

import androidx.compose.runtime.Composable
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.jarvis.ai.ui.screens.auth.LoginScreen
import com.jarvis.ai.ui.screens.auth.RegisterScreen
import com.jarvis.ai.ui.screens.dashboard.DashboardScreen
import com.jarvis.ai.ui.screens.conversations.ConversationsScreen
import com.jarvis.ai.ui.screens.conversations.ConversationDetailScreen
import com.jarvis.ai.ui.screens.settings.SettingsScreen

@Composable
fun JarvisApp() {
    val navController = rememberNavController()
    
    NavHost(
        navController = navController,
        startDestination = "login"
    ) {
        composable("login") {
            LoginScreen(
                onNavigateToRegister = {
                    navController.navigate("register")
                },
                onLoginSuccess = {
                    navController.navigate("dashboard") {
                        popUpTo("login") { inclusive = true }
                    }
                }
            )
        }
        
        composable("register") {
            RegisterScreen(
                onNavigateToLogin = {
                    navController.popBackStack()
                },
                onRegisterSuccess = {
                    navController.navigate("dashboard") {
                        popUpTo("login") { inclusive = true }
                    }
                }
            )
        }
        
        composable("dashboard") {
            DashboardScreen(
                onNavigateToConversations = {
                    navController.navigate("conversations")
                },
                onNavigateToSettings = {
                    navController.navigate("settings")
                }
            )
        }
        
        composable("conversations") {
            ConversationsScreen(
                onNavigateToConversation = { conversationId ->
                    navController.navigate("conversation/$conversationId")
                },
                onBack = {
                    navController.popBackStack()
                }
            )
        }
        
        composable("conversation/{conversationId}") { backStackEntry ->
            val conversationId = backStackEntry.arguments?.getString("conversationId")
            ConversationDetailScreen(
                conversationId = conversationId ?: "",
                onBack = {
                    navController.popBackStack()
                }
            )
        }
        
        composable("settings") {
            SettingsScreen(
                onBack = {
                    navController.popBackStack()
                }
            )
        }
    }
}
